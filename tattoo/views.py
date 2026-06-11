import json
import re
from urllib.parse import urlparse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, Q, Prefetch, Sum
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError, ObjectDoesNotExist
from django.db import DatabaseError
from .models import ServiceCategory, Style, Service, ServicePackage, Artist, ArtistStyle, Portfolio, Booking, Review, ArtistPaymentSettings
from .forms import RegisterForm, BookingForm, ReviewForm
from .payment import (
    generate_payment_session, get_payment_instructions, mark_booking_as_paid,
    verify_payment_proof, expire_payment_if_needed, is_payment_expired,
    method_requires_proof, METHOD_LABELS,
)


# ============================================================
# Custom error handlers — friendly, tidak menakut-nakuti user
# ============================================================
def custom_404(request, exception=None):
    return render(request, 'tattoo/404.html', status=404)


def custom_500(request):
    return render(request, 'tattoo/500.html', status=500)


def home(request):
    categories = ServiceCategory.objects.filter(is_active=True).prefetch_related(
        Prefetch('services', queryset=Service.objects.filter(is_active=True, is_popular=True))
    )
    services_popular = Service.objects.filter(is_active=True, is_popular=True)[:6]
    services_all = Service.objects.filter(is_active=True).select_related(
        'category'
    ).prefetch_related('styles')[:9]
    artists = Artist.objects.filter(is_active=True).prefetch_related(
        'portfolios', 'specialties', 'artist_styles__style'
    )[:8]
    artists_with_rating = []
    for artist in artists:
        avg = Review.objects.filter(booking__artist=artist).aggregate(Avg('rating'))['rating__avg']
        artists_with_rating.append({
            'artist': artist,
            'avg_rating': round(avg, 1) if avg else None,
        })
    stats = {
        'artists_count': Artist.objects.filter(is_active=True).count(),
        'services_count': Service.objects.filter(is_active=True).count(),
        'completed_orders': Booking.objects.filter(status='completed').count(),
        'categories_count': ServiceCategory.objects.filter(is_active=True).count(),
    }
    return render(request, 'tattoo/index.html', {
        'categories': categories,
        'services_popular': services_popular,
        'services_all': services_all,
        'artists_with_rating': artists_with_rating,
        'stats': stats,
    })


def service_list(request):
    categories = ServiceCategory.objects.filter(is_active=True).prefetch_related(
        Prefetch('services', queryset=Service.objects.filter(is_active=True))
    )
    all_styles = Style.objects.filter(is_active=True).order_by('sort_order', 'name')
    return render(request, 'tattoo/services.html', {
        'categories': categories,
        'all_styles': all_styles,
    })


def service_detail(request, service_id):
    service = get_object_or_404(Service, id=service_id, is_active=True)
    packages = ServicePackage.objects.filter(service=service, is_active=True)
    artists = Artist.objects.filter(
        is_active=True, specialties=service
    ).distinct()
    return render(request, 'tattoo/service_detail.html', {
        'service': service,
        'packages': packages,
        'artists': artists,
    })


def artist_list(request):
    artists = Artist.objects.filter(is_active=True).prefetch_related(
        'portfolios', 'specialties', 'artist_styles__style'
    )
    mode = request.GET.get('mode')
    if mode == 'mobile':
        artists = artists.filter(is_available_mobile=True)
    elif mode == 'studio':
        artists = artists.filter(is_available_studio=True)

    artists_data = []
    for artist in artists:
        avg = Review.objects.filter(booking__artist=artist).aggregate(Avg('rating'))['rating__avg']
        review_count = Review.objects.filter(booking__artist=artist).count()
        artists_data.append({
            'artist': artist,
            'avg_rating': round(avg, 1) if avg else None,
            'review_count': review_count,
            'portfolio_count': artist.portfolios.count(),
        })
    all_styles = Style.objects.filter(is_active=True).order_by('sort_order', 'name')
    return render(request, 'tattoo/artists.html', {
        'artists_data': artists_data,
        'all_styles': all_styles,
        'current_mode': mode,
    })


def artist_detail(request, artist_id):
    artist = get_object_or_404(Artist.objects.prefetch_related('specialties'), id=artist_id, is_active=True)
    portfolios = Portfolio.objects.filter(artist=artist)[:12]
    reviews = Review.objects.filter(booking__artist=artist).select_related('user')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    review_count = reviews.count()
    completed_bookings_count = Booking.objects.filter(artist=artist, status='completed').count()
    return render(request, 'tattoo/artist_detail.html', {
        'artist': artist,
        'portfolios': portfolios,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1) if avg_rating else None,
        'review_count': review_count,
        'completed_bookings_count': completed_bookings_count,
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user, artist = form.save_with_role()
            except (DatabaseError, ValidationError, Exception):
                messages.error(
                    request,
                    'Maaf, terjadi gangguan teknis. Silakan coba beberapa saat lagi '
                    'atau hubungi kami jika masalah berlanjut.'
                )
                return render(request, 'tattoo/register.html', {'form': form})
            login(request, user)
            if artist:
                messages.success(
                    request,
                    f'Selamat datang, {artist.nickname}! Profil Artist kamu sudah aktif '
                    'dan tampil di daftar artist utama.'
                )
                return redirect('artist_detail', artist_id=artist.id)
            messages.success(request, 'Selamat! Akunmu berhasil dibuat.')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'tattoo/register.html', {'form': form})


def _safe_next_url(request):
    url = request.GET.get('next', '')
    if not url:
        return 'home'
    parsed = urlparse(url)
    if parsed.netloc or parsed.scheme:
        return 'home'
    if not re.match(r'^/[a-zA-Z0-9_\-/]*$', url):
        return 'home'
    return url


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = authenticate(request, username=username, password=password)
        except (DatabaseError, Exception):
            messages.error(
                request,
                'Maaf, terjadi gangguan teknis. Silakan coba beberapa saat lagi.'
            )
            return render(request, 'tattoo/login.html')
        if user:
            login(request, user)
            messages.success(request, f'Selamat datang kembali, {user.username}!')
            return redirect(_safe_next_url(request))
        messages.error(request, 'Username atau password salah.')
    return render(request, 'tattoo/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'Anda telah logout.')
    return redirect('home')


@login_required
def booking_create(request):
    if request.method == 'POST':
        form = BookingForm(request.POST, request.FILES)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            service = form.cleaned_data['service']
            package = form.cleaned_data.get('package')
            if package:
                booking.total_price = package.price
            else:
                booking.total_price = service.price
            if form.cleaned_data['mode'] == 'mobile':
                travel_fee = form.cleaned_data['artist'].mobile_fee
                booking.travel_fee = travel_fee
                booking.total_price += travel_fee
            booking.save()
            messages.success(request, 'Pesanan berhasil dibuat! Silakan tunggu konfirmasi dari artist.')
            return redirect('booking_detail', booking_id=booking.id)
    else:
        initial = {}
        for key in ('service', 'package', 'artist'):
            value = request.GET.get(key)
            if value and value.isdigit():
                initial[key] = value
        mode = request.GET.get('mode')
        if mode in ('studio', 'mobile'):
            initial['mode'] = mode
        form = BookingForm(initial=initial)

    services = Service.objects.filter(is_active=True).select_related('category').order_by('name')
    artists = Artist.objects.filter(is_active=True).order_by('nickname')
    packages = ServicePackage.objects.filter(is_active=True).select_related('service')

    return render(request, 'tattoo/booking_create.html', {
        'form': form,
        'services': services,
        'artists': artists,
        'packages': packages,
    })


@login_required
def booking_list(request):
    bookings_qs = Booking.objects.filter(user=request.user).select_related(
        'service', 'artist', 'package'
    )

    status_filter = request.GET.get('status', 'all')
    valid_filters = {'all', 'active', 'pending', 'confirmed', 'in_progress',
                     'completed', 'cancelled', 'unpaid'}
    if status_filter not in valid_filters:
        status_filter = 'all'

    if status_filter == 'active':
        bookings = bookings_qs.filter(status__in=['pending', 'confirmed', 'in_progress'])
    elif status_filter == 'unpaid':
        bookings = bookings_qs.filter(payment_status__in=['unpaid', 'pending']).exclude(status='cancelled')
    elif status_filter == 'all':
        bookings = bookings_qs
    else:
        bookings = bookings_qs.filter(status=status_filter)

    stats = {
        'total': bookings_qs.count(),
        'active': bookings_qs.filter(status__in=['pending', 'confirmed', 'in_progress']).count(),
        'completed': bookings_qs.filter(status='completed').count(),
        'unpaid': bookings_qs.filter(payment_status__in=['unpaid', 'pending']).exclude(status='cancelled').count(),
    }

    filter_tabs = [
        ('all', 'Semua', 'bi-collection', stats['total']),
        ('active', 'Aktif', 'bi-hourglass-split', stats['active']),
        ('unpaid', 'Belum Lunas', 'bi-wallet2', stats['unpaid']),
        ('completed', 'Selesai', 'bi-check-circle', stats['completed']),
    ]

    return render(request, 'tattoo/booking_list.html', {
        'bookings': bookings,
        'stats': stats,
        'current_filter': status_filter,
        'filter_tabs': filter_tabs,
    })


@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related('service', 'artist', 'package', 'user'),
        id=booking_id, user=request.user
    )
    review = Review.objects.filter(booking=booking).first()
    review_form = None
    if booking.status == 'completed' and not review:
        if request.method == 'POST':
            review_form = ReviewForm(request.POST)
            if review_form.is_valid():
                Review.objects.create(
                    booking=booking,
                    user=request.user,
                    rating=review_form.cleaned_data['rating'],
                    comment=review_form.cleaned_data['comment'],
                )
                messages.success(request, 'Terima kasih! Ulasanmu sangat berarti bagi kami.')
                return redirect('booking_detail', booking_id=booking.id)
        else:
            review_form = ReviewForm()
    return render(request, 'tattoo/booking_detail.html', {
        'booking': booking,
        'review': review,
        'review_form': review_form,
    })


@login_required
def payment_initiate(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if booking.payment_status == 'paid':
        messages.info(request, 'Pesanan ini sudah lunas.')
        return redirect('booking_detail', booking_id=booking.id)

    if booking.status == 'cancelled':
        messages.warning(request, 'Pesanan ini sudah dibatalkan.')
        return redirect('booking_detail', booking_id=booking.id)

    # Auto-expire jika sudah lewat batas waktu
    if expire_payment_if_needed(booking):
        messages.error(
            request,
            'Batas waktu pembayaran sudah habis. Silakan buat pesanan baru atau hubungi artist.'
        )
        return redirect('booking_detail', booking_id=booking.id)

    # Cek apakah artist menerima pembayaran online
    try:
        pay_settings = booking.artist.payment_settings
        if not pay_settings.accept_online_payment:
            messages.warning(
                request,
                f'Artist {booking.artist.nickname} sedang tidak menerima pembayaran online. '
                'Silakan hubungi artist untuk metode pembayaran lain.'
            )
            return redirect('booking_detail', booking_id=booking.id)
    except ArtistPaymentSettings.DoesNotExist:
        pass  # Default: pembayaran online aktif

    # Generate payment session (transaction_id + expires_at) — idempotent
    generate_payment_session(booking)

    # Jika bukti sebelumnya ditolak → izinkan upload ulang
    rejected_note = None
    if booking.payment_verification_status == 'rejected':
        rejected_note = booking.payment_verification_note

    selected_method = request.GET.get('method', '').strip()
    selected_brand = request.GET.get('brand', '').strip().lower()
    instructions = None
    if selected_method and selected_method in METHOD_LABELS:
        accounts = dict(settings.PLATFORM_PAYMENT_ACCOUNTS)
        if selected_method == 'credit_card':
            try:
                ps = booking.artist.payment_settings
                accounts['credit_card'] = {
                    'processing_method': ps.card_processing_method or 'manual',
                    'payment_link': ps.card_payment_link or '',
                    'fee_percent': float(ps.card_fee_percent or 0),
                    'note': ps.card_note or '',
                }
            except ArtistPaymentSettings.DoesNotExist:
                accounts['credit_card'] = {
                    'processing_method': 'manual',
                    'payment_link': '',
                    'fee_percent': 0,
                    'note': '',
                }
        elif selected_method == 'qris':
            try:
                ps = booking.artist.payment_settings
                accounts['qris'] = {
                    'merchant_name': ps.qris_merchant_name or (ps.artist.nickname if hasattr(ps, 'artist') else 'Merchant'),
                    'image_url': ps.qris_image.url if ps.qris_image else '',
                    'fee_percent': float(ps.qris_fee_percent or 0),
                    'note': ps.qris_note or '',
                }
            except ArtistPaymentSettings.DoesNotExist:
                accounts['qris'] = {
                    'merchant_name': 'Merchant',
                    'image_url': '',
                    'fee_percent': 0.7,
                    'note': '',
                }
        instructions = get_payment_instructions(
            selected_method, booking, accounts
        )

    return render(request, 'tattoo/payment_page.html', {
        'booking': booking,
        'instructions': instructions,
        'selected_method': selected_method,
        'selected_brand': selected_brand,
        'enabled_methods': _get_enabled_methods_for_artist(booking.artist),
        'method_labels': METHOD_LABELS,
        'card_processing_method': accounts.get('credit_card', {}).get('processing_method', 'manual') if selected_method == 'credit_card' else None,
        'verification_pending': booking.payment_verification_status == 'pending',
        'rejected_note': rejected_note,
        'is_expired': is_payment_expired(booking),
    })


@login_required
@require_POST
def payment_confirm(request, booking_id):
    """Customer submit konfirmasi + (jika wajib) upload bukti pembayaran."""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if booking.payment_status == 'paid':
        messages.info(request, 'Pesanan ini sudah lunas.')
        return redirect('booking_detail', booking_id=booking.id)

    if booking.status == 'cancelled':
        messages.warning(request, 'Pesanan sudah dibatalkan.')
        return redirect('booking_detail', booking_id=booking.id)

    # Cek expiry
    if is_payment_expired(booking):
        expire_payment_if_needed(booking)
        messages.error(
            request,
            'Batas waktu pembayaran sudah habis. Pesanan dianggap gagal.'
        )
        return redirect('booking_detail', booking_id=booking.id)

    method = (request.POST.get('method') or '').strip()
    requires_proof = method_requires_proof(method)
    proof_file = request.FILES.get('payment_proof') if requires_proof else None

    # Validasi tambahan khusus metode retail/kartu
    if requires_proof:
        if not proof_file:
            messages.error(
                request,
                'Bukti pembayaran (foto struk / screenshot) wajib diupload untuk metode ini.'
            )
            return redirect('payment_initiate', booking_id=booking.id)
        # Validasi tipe & ukuran file
        allowed_types = {'image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/heic', 'image/heif'}
        if proof_file.content_type not in allowed_types:
            messages.error(request, 'Format bukti pembayaran harus JPG, PNG, atau WEBP.')
            return redirect('payment_initiate', booking_id=booking.id)
        if proof_file.size > 5 * 1024 * 1024:
            messages.error(request, 'Ukuran bukti pembayaran maksimal 5 MB.')
            return redirect('payment_initiate', booking_id=booking.id)

    # Persetujuan SOP (wajib untuk metode yang butuh bukti)
    if requires_proof and request.POST.get('sop_agreement') != '1':
        messages.error(
            request,
            'Kamu harus menyetujui pernyataan bahwa bukti pembayaran yang diupload adalah benar.'
        )
        return redirect('payment_initiate', booking_id=booking.id)

    success, error = mark_booking_as_paid(booking, method, proof_file=proof_file)
    if not success:
        messages.error(request, error or 'Gagal memproses pembayaran.')
        return redirect('payment_initiate', booking_id=booking.id)

    if requires_proof:
        messages.success(
            request,
            f'Bukti pembayaran via {booking.payment_method} berhasil dikirim! '
            'Booking kamu akan dikonfirmasi setelah artist memverifikasi bukti pembayaran. '
            'Estimasi verifikasi 1–2 jam pada jam kerja.'
        )
    else:
        messages.success(
            request,
            f'Pembayaran berhasil via {booking.payment_method}! Pesananmu sudah dikonfirmasi.'
        )
    return redirect('booking_detail', booking_id=booking.id)


@login_required
@require_POST
def payment_verify(request, booking_id):
    """Artist approve / reject bukti pembayaran customer."""
    artist = _get_artist_or_404(request.user)
    booking = get_object_or_404(
        Booking.objects.select_related('user', 'service'),
        id=booking_id, artist=artist
    )

    action = (request.POST.get('action') or '').strip().lower()
    note = (request.POST.get('note') or '').strip()

    success, error = verify_payment_proof(booking, action, note, by=request.user)
    if not success:
        messages.error(request, error or 'Gagal memproses verifikasi.')
        return redirect('artist_booking_detail', booking_id=booking.id)

    if action == 'approve':
        messages.success(
            request,
            f'Pembayaran pesanan #{booking.id} disetujui. Status booking: Dikonfirmasi.'
        )
    else:
        messages.warning(
            request,
            f'Pembayaran pesanan #{booking.id} ditolak. Customer akan diminta upload ulang.'
        )
    return redirect('artist_booking_detail', booking_id=booking.id)


def _get_enabled_methods_for_artist(artist):
    """Return dict of method-group -> enabled, sesuai settingan artist."""
    try:
        s = artist.payment_settings
    except ArtistPaymentSettings.DoesNotExist:
        s = None
    return {
        'bank_va': (s.enable_bank_va if s else True),
        'ewallet': (s.enable_ewallet if s else True),
        'credit_card': (s.enable_credit_card if s else False),
        'convenience_store': (s.enable_convenience_store if s else True),
        'qris': (getattr(s, 'enable_qris', False) if s else False),
    }


def _get_artist_or_404(user):
    try:
        return user.artist
    except ObjectDoesNotExist:
        raise PermissionDenied('Anda bukan seorang tattoo artist.')


@login_required
def artist_dashboard(request):
    artist = _get_artist_or_404(request.user)
    bookings_qs = Booking.objects.filter(artist=artist).select_related(
        'user', 'service', 'package'
    )

    total_bookings = bookings_qs.count()
    pending_count = bookings_qs.filter(status='pending').count()
    confirmed_count = bookings_qs.filter(status='confirmed').count()
    in_progress_count = bookings_qs.filter(status='in_progress').count()
    completed_count = bookings_qs.filter(status='completed').count()
    cancelled_count = bookings_qs.filter(status='cancelled').count()

    total_revenue = bookings_qs.filter(
        payment_status='paid'
    ).aggregate(total=Sum('total_price'))['total'] or 0

    recent_bookings = bookings_qs.order_by('-created_at')[:5]
    latest_reviews = Review.objects.filter(booking__artist=artist).select_related(
        'user', 'booking'
    ).order_by('-created_at')[:5]

    context = {
        'artist': artist,
        'total_bookings': total_bookings,
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'total_revenue': total_revenue,
        'recent_bookings': recent_bookings,
        'latest_reviews': latest_reviews,
    }
    return render(request, 'tattoo/artist_dashboard.html', context)


@login_required
def artist_booking_list(request):
    artist = _get_artist_or_404(request.user)
    status_filter = request.GET.get('status', 'all')

    qs = Booking.objects.filter(artist=artist).select_related(
        'user', 'service', 'package'
    ).order_by('-booking_date', '-booking_time')

    valid_filters = {
        'all': lambda q: q,
        'pending': lambda q: q.filter(status='pending'),
        'confirmed': lambda q: q.filter(status='confirmed'),
        'in_progress': lambda q: q.filter(status='in_progress'),
        'completed': lambda q: q.filter(status='completed'),
        'cancelled': lambda q: q.filter(status='cancelled'),
        'unpaid': lambda q: q.filter(payment_status__in=['unpaid', 'pending']).exclude(status='cancelled'),
    }
    bookings = valid_filters.get(status_filter, valid_filters['all'])(qs)

    context = {
        'artist': artist,
        'bookings': bookings,
        'current_filter': status_filter,
        'filter_tabs': [
            ('all', 'Semua', 'bi-collection'),
            ('pending', 'Menunggu', 'bi-hourglass-split'),
            ('confirmed', 'Dikonfirmasi', 'bi-check-circle'),
            ('in_progress', 'Diproses', 'bi-gear'),
            ('completed', 'Selesai', 'bi-check-all'),
            ('cancelled', 'Dibatalkan', 'bi-x-circle'),
        ],
    }
    return render(request, 'tattoo/artist_bookings.html', context)


@login_required
def artist_booking_detail(request, booking_id):
    artist = _get_artist_or_404(request.user)
    booking = get_object_or_404(
        Booking.objects.select_related('user', 'service', 'package'),
        id=booking_id, artist=artist
    )
    review = Review.objects.filter(booking=booking).first()

    context = {
        'artist': artist,
        'booking': booking,
        'review': review,
    }
    return render(request, 'tattoo/artist_booking_detail.html', context)


@login_required
def artist_update_status(request, booking_id):
    if request.method != 'POST':
        return redirect('artist_booking_detail', booking_id=booking_id)

    artist = _get_artist_or_404(request.user)
    booking = get_object_or_404(Booking, id=booking_id, artist=artist)
    new_status = request.POST.get('status', '')

    VALID_TRANSITIONS = {
        'pending': ['confirmed', 'cancelled'],
        'confirmed': ['in_progress', 'cancelled'],
        'in_progress': ['completed', 'cancelled'],
        'completed': [],
        'cancelled': [],
    }

    allowed = VALID_TRANSITIONS.get(booking.status, [])
    if new_status not in allowed:
        messages.error(request, f'Tidak bisa mengubah status dari "{booking.get_status_display()}" ke "{dict(Booking.STATUS_CHOICES).get(new_status, new_status)}".')
        return redirect('artist_booking_detail', booking_id=booking.id)

    booking.status = new_status
    booking.save()

    status_labels = dict(Booking.STATUS_CHOICES)
    messages.success(request, f'Pesanan {booking.id} berhasil diubah ke "{status_labels.get(new_status, new_status)}".')
    return redirect('artist_booking_detail', booking_id=booking.id)


@login_required
def artist_profile_edit(request):
    artist = _get_artist_or_404(request.user)
    if request.method == 'POST':
        artist.nickname = request.POST.get('nickname', '').strip()
        artist.name = request.POST.get('name', '').strip()
        try:
            artist.experience_years = int(request.POST.get('experience_years', artist.experience_years))
        except (ValueError, TypeError):
            pass
        artist.service_area = request.POST.get('service_area', '').strip()
        artist.short_bio = request.POST.get('short_bio', '').strip()
        artist.bio = request.POST.get('bio', '').strip()
        artist.instagram = request.POST.get('instagram', '').strip()
        photo = request.FILES.get('photo')
        if photo:
            if photo.size > 10 * 1024 * 1024:
                messages.error(request, 'Ukuran foto maksimal 10 MB.')
                return redirect('artist_profile_edit')
            artist.photo = photo
        artist.save()
        messages.success(request, 'Profil berhasil diperbarui!')
        return redirect('artist_profile_edit')
    return render(request, 'tattoo/artist_profile_edit.html', {'artist': artist})


@login_required
def artist_portfolio(request):
    artist = _get_artist_or_404(request.user)
    portfolios = Portfolio.objects.filter(artist=artist).order_by('-created_at')
    all_services = Service.objects.filter(is_active=True)
    return render(request, 'tattoo/artist_portfolio.html', {
        'artist': artist,
        'portfolios': portfolios,
        'all_services': all_services,
    })


@login_required
def artist_portfolio_add(request):
    if request.method != 'POST':
        return redirect('artist_portfolio')
    artist = _get_artist_or_404(request.user)
    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '').strip()
    service_id = request.POST.get('service', '')
    image = request.FILES.get('image')
    if not title:
        messages.error(request, 'Judul karya tidak boleh kosong.')
        return redirect('artist_portfolio')
    if not image:
        messages.error(request, 'Gambar wajib diupload.')
        return redirect('artist_portfolio')
    # Validasi format gambar
    allowed_types = {'image/jpeg', 'image/jpg', 'image/png', 'image/webp'}
    if image.content_type not in allowed_types:
        messages.error(request, 'Format gambar harus JPG, PNG, atau WEBP.')
        return redirect('artist_portfolio')
    if image.size > 10 * 1024 * 1024:
        messages.error(request, 'Ukuran gambar maksimal 10 MB.')
        return redirect('artist_portfolio')
    service = None
    if service_id and service_id.isdigit():
        service = Service.objects.filter(id=int(service_id)).first()
    try:
        Portfolio.objects.create(
            artist=artist,
            title=title,
            description=description,
            service=service,
            image=image,
        )
    except Exception:
        messages.error(request, 'Gagal menyimpan gambar. Coba lagi atau hubungi kami.')
        return redirect('artist_portfolio')
    messages.success(request, 'Karya berhasil ditambahkan ke portofolio!')
    return redirect('artist_portfolio')


@login_required
def artist_portfolio_delete(request, portfolio_id):
    if request.method != 'POST':
        return redirect('artist_portfolio')
    artist = _get_artist_or_404(request.user)
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, artist=artist)
    portfolio.delete()
    messages.success(request, 'Karya berhasil dihapus.')
    return redirect('artist_portfolio')


@login_required
def artist_settings(request):
    artist = _get_artist_or_404(request.user)
    if request.method == 'POST':
        artist.is_available_studio = request.POST.get('is_available_studio') == '1'
        artist.is_available_mobile = request.POST.get('is_available_mobile') == '1'
        artist.mobile_fee = request.POST.get('mobile_fee', artist.mobile_fee)
        artist.service_area = request.POST.get('service_area', artist.service_area)
        artist.save()
        messages.success(request, 'Pengaturan berhasil disimpan!')
        return redirect('artist_settings')
    all_services = Service.objects.filter(is_active=True).order_by('category__name', 'name')
    all_styles = Style.objects.filter(is_active=True).order_by('sort_order', 'name')
    return render(request, 'tattoo/artist_settings.html', {
        'artist': artist,
        'all_services': all_services,
        'all_styles': all_styles,
    })


@login_required
def artist_settings_specialties(request):
    if request.method != 'POST':
        return redirect('artist_settings')
    artist = _get_artist_or_404(request.user)
    specialty_ids = request.POST.getlist('specialties')
    if specialty_ids:
        services = Service.objects.filter(id__in=[int(x) for x in specialty_ids if x.isdigit()])
        artist.specialties.set(services)
    else:
        artist.specialties.clear()
    artist.save()
    messages.success(request, 'Spesialisasi berhasil diperbarui!')
    return redirect('artist_settings')


@login_required
def artist_settings_styles(request):
    if request.method != 'POST':
        return redirect('artist_settings')
    artist = _get_artist_or_404(request.user)
    style_ids = request.POST.getlist('styles')
    experience_data = {}

    for key, value in request.POST.items():
        if key.startswith('exp_'):
            sid = key.replace('exp_', '')
            if sid.isdigit():
                try:
                    experience_data[int(sid)] = int(value)
                except (ValueError, TypeError):
                    experience_data[int(sid)] = 0

    skill_data = {}
    for key, value in request.POST.items():
        if key.startswith('skill_'):
            sid = key.replace('skill_', '')
            if sid.isdigit() and value in ['beginner', 'intermediate', 'advanced', 'master']:
                skill_data[int(sid)] = value

    primary_style_id = request.POST.get('primary_style', '')
    primary_id = int(primary_style_id) if primary_style_id.isdigit() else None

    if style_ids:
        styles = Style.objects.filter(id__in=[int(x) for x in style_ids if x.isdigit()])
        current_ids = set(artist.style_expertise.values_list('style_id', flat=True))
        new_ids = set(s.id for s in styles)

        # Remove unselected
        for old_id in current_ids - new_ids:
            ArtistStyle.objects.filter(artist=artist, style_id=old_id).delete()

        # Add or update selected
        for style in styles:
            years = experience_data.get(style.id, 0)
            skill = skill_data.get(style.id, 'intermediate')
            is_primary = (style.id == primary_id)

            ArtistStyle.objects.update_or_create(
                artist=artist, style=style,
                defaults={
                    'experience_years': years,
                    'skill_level': skill,
                    'is_primary': is_primary,
                },
            )
    else:
        artist.style_expertise.clear()

    artist.save()
    messages.success(request, 'Keahlian style tattoo berhasil diperbarui!')
    return redirect('artist_settings')


@login_required
def artist_toggle_service(request, service_id):
    if request.method != 'POST':
        return redirect('artist_services')
    artist = _get_artist_or_404(request.user)
    service = get_object_or_404(Service, id=service_id, is_active=True)
    activated = False
    if service in artist.specialties.all():
        artist.specialties.remove(service)
    else:
        artist.specialties.add(service)
        activated = True
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'activated': activated, 'active_count': artist.specialties.count()})
    return redirect('artist_services')


@login_required
def artist_services(request):
    artist = _get_artist_or_404(request.user)
    specialties = list(artist.specialties.all())
    all_services = Service.objects.filter(is_active=True).select_related('category').prefetch_related('styles').order_by('category__sort_order', 'category__name', 'name')
    categories = ServiceCategory.objects.filter(is_active=True).prefetch_related(
        'services'
    ).order_by('sort_order', 'name')
    active_counts = {}
    for cat in categories:
        active_counts[cat.id] = sum(1 for s in cat.services.all() if s in specialties)
    inactive_count = all_services.count() - len(specialties)
    return render(request, 'tattoo/artist_services.html', {
        'artist': artist,
        'specialties': specialties,
        'all_services': all_services,
        'categories': categories,
        'active_counts': active_counts,
        'inactive_count': inactive_count,
    })


@login_required
def artist_payment_settings(request):
    """Halaman pengaturan payment gateway untuk artist."""
    artist = _get_artist_or_404(request.user)
    settings_obj, _ = ArtistPaymentSettings.objects.get_or_create(artist=artist)

    if request.method == 'POST':
        # ===== Gateway =====
        settings_obj.accept_online_payment = request.POST.get('accept_online_payment') == '1'
        settings_obj.enable_bank_va = request.POST.get('enable_bank_va') == '1'
        settings_obj.enable_ewallet = request.POST.get('enable_ewallet') == '1'
        settings_obj.enable_credit_card = request.POST.get('enable_credit_card') == '1'
        settings_obj.enable_convenience_store = request.POST.get('enable_convenience_store') == '1'
        settings_obj.enable_qris = request.POST.get('enable_qris') == '1'

        # ===== Per-bank / per-ewallet =====
        settings_obj.enable_bca = request.POST.get('enable_bca') == '1'
        settings_obj.enable_mandiri = request.POST.get('enable_mandiri') == '1'
        settings_obj.enable_bni = request.POST.get('enable_bni') == '1'
        settings_obj.enable_bri = request.POST.get('enable_bri') == '1'
        settings_obj.enable_permata = request.POST.get('enable_permata') == '1'
        settings_obj.enable_cimb = request.POST.get('enable_cimb') == '1'

        settings_obj.enable_gopay = request.POST.get('enable_gopay') == '1'
        settings_obj.enable_ovo = request.POST.get('enable_ovo') == '1'
        settings_obj.enable_dana = request.POST.get('enable_dana') == '1'
        settings_obj.enable_shopeepay = request.POST.get('enable_shopeepay') == '1'
        settings_obj.enable_linkaja = request.POST.get('enable_linkaja') == '1'

        # ===== Bank accounts =====
        for bank in ('bca', 'mandiri', 'bni', 'bri', 'permata', 'cimb'):
            num = (request.POST.get(f'bank_{bank}_number') or '').strip() or None
            name = (request.POST.get(f'bank_{bank}_name') or '').strip() or None
            setattr(settings_obj, f'bank_{bank}_number', num)
            setattr(settings_obj, f'bank_{bank}_name', name)

        # ===== E-wallet =====
        for e in ('gopay', 'ovo', 'dana', 'shopeepay', 'linkaja'):
            setattr(settings_obj, f'ewallet_{e}', (request.POST.get(f'ewallet_{e}') or '').strip() or None)

        # ===== Fees =====
        def _pct(name, default=0, lo=0, hi=100):
            try:
                v = (request.POST.get(name, str(default)) or str(default)).strip() or str(default)
                return max(lo, min(hi, float(v)))
            except (ValueError, TypeError):
                return default

        settings_obj.platform_fee_percent = _pct('platform_fee_percent')
        settings_obj.card_fee_percent     = _pct('card_fee_percent')
        settings_obj.va_fee_percent       = _pct('va_fee_percent')
        settings_obj.ewallet_fee_percent  = _pct('ewallet_fee_percent')
        settings_obj.retail_fee_percent   = _pct('retail_fee_percent')
        settings_obj.qris_fee_percent     = _pct('qris_fee_percent', default=0.7, lo=0, hi=10)

        # ===== Card config =====
        valid_card_methods = {choice[0] for choice in ArtistPaymentSettings.CARD_METHOD_CHOICES}
        card_method = (request.POST.get('card_processing_method') or '').strip()
        settings_obj.card_processing_method = card_method if card_method in valid_card_methods else None
        settings_obj.card_payment_link = (request.POST.get('card_payment_link') or '').strip() or None
        settings_obj.card_note = (request.POST.get('card_note') or '').strip() or None

        # ===== QRIS =====
        settings_obj.qris_merchant_name = (request.POST.get('qris_merchant_name') or '').strip() or None
        settings_obj.qris_note = (request.POST.get('qris_note') or '').strip() or None
        if request.FILES.get('qris_image'):
            settings_obj.qris_image = request.FILES['qris_image']
        if request.POST.get('qris_image_clear') == '1':
            settings_obj.qris_image = None

        # ===== Behavior =====
        valid_confirm = {c[0] for c in ArtistPaymentSettings.CONFIRMATION_CHOICES}
        cm = (request.POST.get('confirmation_mode') or 'manual').strip()
        settings_obj.confirmation_mode = cm if cm in valid_confirm else 'manual'

        try:
            settings_obj.payment_expiry_hours = max(1, min(168, int(request.POST.get('payment_expiry_hours', 24) or 24)))
        except (ValueError, TypeError):
            settings_obj.payment_expiry_hours = 24

        try:
            min_amt = (request.POST.get('min_payment_amount') or '0').strip() or '0'
            settings_obj.min_payment_amount = max(0, float(min_amt))
        except (ValueError, TypeError):
            settings_obj.min_payment_amount = 0

        # ===== Working hours =====
        settings_obj.accept_payment_247 = request.POST.get('accept_payment_247') == '1'
        from datetime import time as _time
        for fname, default in (('working_hours_start', '08:00'), ('working_hours_end', '22:00')):
            raw = (request.POST.get(fname) or default).strip()
            try:
                h, m = raw.split(':')[:2]
                setattr(settings_obj, fname, _time(int(h), int(m)))
            except (ValueError, AttributeError, TypeError):
                setattr(settings_obj, fname, _time(*map(int, default.split(':'))))

        # ===== Notifications =====
        ne = (request.POST.get('notification_email') or '').strip() or None
        settings_obj.notification_email = ne or None
        nw = (request.POST.get('notification_whatsapp') or '').strip() or None
        settings_obj.notification_whatsapp = nw or None
        settings_obj.notify_on_pending = request.POST.get('notify_on_pending') == '1'
        settings_obj.notify_on_paid    = request.POST.get('notify_on_paid') == '1'
        settings_obj.notify_on_failed  = request.POST.get('notify_on_failed') == '1'
        settings_obj.notify_on_expired = request.POST.get('notify_on_expired') == '1'

        # ===== Notes / policies =====
        settings_obj.general_payment_note = (request.POST.get('general_payment_note') or '').strip() or None
        settings_obj.refund_policy = (request.POST.get('refund_policy') or '').strip() or None
        settings_obj.terms_accepted = request.POST.get('terms_accepted') == '1'

        # ===== Midtrans (existing) =====
        settings_obj.use_split_payment = request.POST.get('use_split_payment') == '1'
        mid = (request.POST.get('midtrans_merchant_id') or '').strip() or None
        settings_obj.midtrans_merchant_id = mid

        settings_obj.save()
        messages.success(request, 'Pengaturan payment gateway berhasil disimpan!')
        return redirect('artist_payment_settings')

    # ===== Stats =====
    bank_count = sum(1 for f in [settings_obj.bank_bca_number, settings_obj.bank_mandiri_number,
                                  settings_obj.bank_bni_number, settings_obj.bank_bri_number,
                                  settings_obj.bank_permata_number, settings_obj.bank_cimb_number] if f)
    ewallet_count = sum(1 for f in [settings_obj.ewallet_gopay, settings_obj.ewallet_ovo,
                                    settings_obj.ewallet_dana, settings_obj.ewallet_shopeepay,
                                    settings_obj.ewallet_linkaja] if f)

    enabled_method_flags = [
        settings_obj.enable_bank_va, settings_obj.enable_ewallet,
        settings_obj.enable_credit_card, settings_obj.enable_convenience_store,
        settings_obj.enable_qris,
    ]
    method_count = sum(1 for f in enabled_method_flags if f)

    return render(request, 'tattoo/artist_payment_settings.html', {
        'artist': artist,
        'settings': settings_obj,
        'enabled_count': len(settings_obj.get_enabled_methods()),
        'stats': {
            'bank_count': bank_count,
            'ewallet_count': ewallet_count,
            'method_count': method_count,
            'method_total': 5,
        },
        'bank_options': [
            ('bca', 'BCA', 'tattoo/img/payments/bca.svg'),
            ('mandiri', 'Mandiri', 'tattoo/img/payments/mandiri.svg'),
            ('bni', 'BNI', 'tattoo/img/payments/bni.svg'),
            ('bri', 'BRI', 'tattoo/img/payments/bri.svg'),
            ('permata', 'Permata', 'tattoo/img/payments/permata.svg'),
            ('cimb', 'CIMB Niaga', 'tattoo/img/payments/cimb.svg'),
        ],
        'ewallet_options': [
            ('gopay', 'GoPay', 'tattoo/img/payments/gopay.svg'),
            ('ovo', 'OVO', 'tattoo/img/payments/ovo.svg'),
            ('dana', 'DANA', 'tattoo/img/payments/dana.svg'),
            ('shopeepay', 'ShopeePay', 'tattoo/img/payments/shopeepay.svg'),
            ('linkaja', 'LinkAja', 'tattoo/img/payments/linkaja.svg'),
        ],
    })
