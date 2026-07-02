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
from django.utils import timezone
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
    try:
        return render(request, 'tattoo/404.html', status=404)
    except Exception:
        from django.http import HttpResponse
        return HttpResponse('<html lang="id"><body style="background:#050505;color:#e0d5c0;display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:sans-serif"><div style="text-align:center"><h2 style="color:#c9a13b">Halaman Tidak Ditemukan</h2><p style="color:#a09880">Halaman yang kamu tuju tidak tersedia.</p><a href="/" style="color:#c9a13b">Kembali ke Beranda</a></div></body></html>', status=404)


def custom_500(request, exception=None):
    try:
        return render(request, 'tattoo/500.html', status=500)
    except Exception:
        import traceback, sys
        tb = traceback.format_exc()
        path = request.path if hasattr(request, 'path') else '?'
        err = ''
        if exception:
            err += f'<p><strong>Exception:</strong> {exception}</p>'
        err += f'<p><strong>Path:</strong> {path}</p>'
        if tb and tb != 'NoneType: None\n':
            safe = tb.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
            err += f'<hr><pre style="font-size:12px;text-align:left;max-width:800px;overflow:auto">{safe}</pre>'
        from django.http import HttpResponse
        return HttpResponse(f'<html lang="id"><body style="background:#050505;color:#e0d5c0;display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:sans-serif"><div style="text-align:center"><h2 style="color:#c9a13b">Mohon Maaf</h2><p style="color:#a09880">Permintaanmu tidak bisa diproses saat ini. Silakan coba beberapa saat lagi.</p>{err}<a href="/" style="color:#c9a13b">Kembali ke Beranda</a></div></body></html>', status=500)


def home(request):
    from django.db import DatabaseError as _DBErr
    from django.core.cache import cache
    try:
        categories = ServiceCategory.objects.filter(is_active=True).prefetch_related(
            Prefetch('services', queryset=Service.objects.filter(is_active=True, is_popular=True))
        )
    except _DBErr:
        categories = []
    try:
        services_popular = Service.objects.filter(is_active=True, is_popular=True).prefetch_related('styles')[:6]
    except _DBErr:
        services_popular = []
    try:
        artists = Artist.objects.filter(is_active=True).prefetch_related(
            'portfolios', 'specialties', 'artist_styles__style'
        ).annotate(
            avg_rating=Avg('bookings__review__rating')
        )[:8]
    except _DBErr:
        artists = []
    artists_with_rating = []
    for artist in artists:
        artists_with_rating.append({
            'artist': artist,
            'avg_rating': round(artist.avg_rating, 1) if artist.avg_rating else None,
        })
    stats = cache.get('home_stats')
    if stats is None:
        try:
            stats = {
                'artists_count': Artist.objects.filter(is_active=True).count(),
                'services_count': Service.objects.filter(is_active=True).count(),
                'completed_orders': Booking.objects.filter(status='completed').count(),
                'categories_count': ServiceCategory.objects.filter(is_active=True).count(),
            }
            cache.set('home_stats', stats, 600)
        except _DBErr:
            stats = {}
    return render(request, 'tattoo/index.html', {
        'categories': categories,
        'services_popular': services_popular,
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
    ).annotate(
        avg_rating=Avg('bookings__review__rating'),
        review_count=Count('bookings__review'),
    )
    mode = request.GET.get('mode')
    if mode == 'mobile':
        artists = artists.filter(is_available_mobile=True)
    elif mode == 'studio':
        artists = artists.filter(is_available_studio=True)

    artists_data = []
    for artist in artists:
        artists_data.append({
            'artist': artist,
            'avg_rating': round(artist.avg_rating, 1) if artist.avg_rating else None,
            'review_count': artist.review_count,
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
            except Exception:
                messages.error(
                    request,
                    'Maaf, terjadi gangguan teknis. Silakan coba beberapa saat lagi '
                    'atau hubungi kami jika masalah berlanjut.'
                )
                return render(request, 'tattoo/register.html', {'form': form})
            try:
                login(request, user)
            except Exception:
                messages.error(
                    request,
                    'Maaf, terjadi gangguan teknis. Silakan coba beberapa saat lagi.'
                )
                return render(request, 'tattoo/register.html', {'form': form})
            if artist:
                messages.success(
                    request,
                    f'Selamat datang, {artist.nickname}! Profil Artist kamu sudah aktif '
                    'dan tampil di daftar artist utama.'
                )
                try:
                    return redirect('artist_detail', artist_id=artist.id)
                except Exception:
                    return redirect('home')
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


def ping(request):
    from django.http import HttpResponse
    return HttpResponse('OK', content_type='text/plain')


def login_view(request):
    try:
        if request.user.is_authenticated:
            return redirect('home')
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            try:
                user = authenticate(request, username=username, password=password)
            except Exception:
                messages.error(request, 'Maaf, terjadi gangguan teknis. Silakan coba beberapa saat lagi.')
                return _render_login(request)
            if user:
                try:
                    login(request, user)
                except Exception:
                    messages.error(request, 'Maaf, terjadi gangguan teknis. Silakan coba beberapa saat lagi.')
                    return _render_login(request)
                messages.success(request, f'Selamat datang kembali, {user.username}!')
                try:
                    target = _safe_next_url(request)
                    if target == 'home':
                        try:
                            if user.artist is not None:
                                target = 'artist_dashboard'
                        except Exception:
                            pass
                    return redirect(target)
                except Exception:
                    return redirect('home')
            messages.error(request, 'Username atau password salah.')
        return _render_login(request)
    except Exception:
        return _render_login_failsafe()


def _render_login(request):
    try:
        return render(request, 'tattoo/login.html', {})
    except Exception:
        return _render_login_failsafe()


def _render_login_failsafe():
    from django.http import HttpResponse
    return HttpResponse("""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mohon Maaf - Bali Ink Hub</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Playfair+Display:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  body { font-family: 'Inter', sans-serif; background: #050505; color: #e0d5c0; min-height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; margin: 0; padding: 20px; }
  .card { background: rgba(255,255,255,0.03); border: 1px solid rgba(201,161,59,0.2); border-radius: 16px; padding: 40px; width: 100%; max-width: 420px; text-align: center; }
  h2 { font-family: 'Playfair Display', serif; color: #c9a13b; }
  p { color: #a09880; line-height: 1.6; }
  .btn { display: inline-block; background: linear-gradient(135deg, #c9a13b, #a8842e); color: #050505; border: none; padding: 12px 32px; border-radius: 8px; font-weight: 600; cursor: pointer; text-decoration: none; margin-top: 8px; }
  .btn:hover { background: linear-gradient(135deg, #dbb34a, #b89434); }
</style>
</head>
<body>
  <div class="card">
    <h2>Mohon Maaf</h2>
    <p>Sistem sedang sibuk. Silakan muat ulang halaman atau coba beberapa saat lagi.</p>
    <a href="/login/" class="btn">Muat Ulang</a>
  </div>
</body>
</html>""")


def logout_view(request):
    logout(request)
    messages.info(request, 'Anda telah logout.')
    return redirect('home')


@login_required
def booking_create(request):
    from django.core.cache import cache as _cache

    services = _cache.get('bc_services')
    artists = _cache.get('bc_artists')
    packages = _cache.get('bc_packages')

    if services is None:
        try:
            services_qs = Service.objects.filter(is_active=True).only(
                'id', 'name', 'price', 'duration', 'category_id'
            ).select_related('category').order_by('name')
            artists_qs = Artist.objects.filter(is_active=True).only(
                'id', 'nickname', 'name', 'is_available_studio', 'is_available_mobile', 'mobile_fee'
            ).order_by('nickname')
            packages_qs = ServicePackage.objects.filter(is_active=True).only(
                'id', 'service_id', 'name', 'price', 'duration'
            ).select_related('service').order_by('price')
        except Exception:
            messages.error(request, 'Maaf, terjadi gangguan. Silakan coba beberapa saat lagi.')
            return redirect('home')

        services = list(services_qs)
        artists = list(artists_qs)
        packages = list(packages_qs)
        _cache.set('bc_services', services, 300)
        _cache.set('bc_artists', artists, 300)
        _cache.set('bc_packages', packages, 300)

        # Reuse the same evaluated querysets for the form (0 extra queries)
        prefetched = {
            'services_qs': services_qs,
            'artists_qs': artists_qs,
            'packages_qs': packages_qs,
        }
    else:
        # Cache hit: minimal PK lookups from cached IDs
        svc_ids = [s.id for s in services]
        art_ids = [a.id for a in artists]
        pkg_ids = [p.id for p in packages]
        prefetched = {
            'services_qs': Service.objects.filter(id__in=svc_ids).only('id','name','price','duration','category_id') if svc_ids else Service.objects.none(),
            'artists_qs': Artist.objects.filter(id__in=art_ids).only('id','nickname','name','is_available_studio','is_available_mobile','mobile_fee') if art_ids else Artist.objects.none(),
            'packages_qs': ServicePackage.objects.filter(id__in=pkg_ids).only('id','service_id','name','price','duration') if pkg_ids else ServicePackage.objects.none(),
        }

    if request.method == 'POST':
        form = BookingForm(request.POST, request.FILES, _prefetched=prefetched)
        if form.is_valid():
            try:
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
            except Exception:
                messages.error(request, 'Maaf, terjadi gangguan saat menyimpan. Silakan coba lagi.')
                return render(request, 'tattoo/booking_create.html', {
                    'form': form, 'services': services, 'artists': artists, 'packages': packages,
                })
    else:
        initial = {}
        for key in ('service', 'package', 'artist'):
            value = request.GET.get(key)
            if value and value.isdigit():
                initial[key] = value
        mode = request.GET.get('mode')
        if mode in ('studio', 'mobile'):
            initial['mode'] = mode
        form = BookingForm(initial=initial, _prefetched=prefetched)

    booking_json = json.dumps({
        'services': [{'id': s.id, 'name': s.name, 'price': int(s.price), 'duration': s.duration} for s in services],
        'packages': [{'id': p.id, 'service_id': p.service_id, 'name': p.name, 'price': int(p.price), 'duration': p.duration} for p in packages],
        'artists': [{'id': a.id, 'nickname': a.nickname, 'name': a.name, 'studio': a.is_available_studio, 'mobile': a.is_available_mobile, 'mobile_fee': int(a.mobile_fee)} for a in artists],
    })

    return render(request, 'tattoo/booking_create.html', {
        'form': form,
        'services': services,
        'artists': artists,
        'packages': packages,
        'booking_json': booking_json,
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

    stats = Booking.objects.filter(user=request.user).aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(status__in=['pending', 'confirmed', 'in_progress'])),
        completed=Count('id', filter=Q(status='completed')),
        unpaid=Count('id', filter=Q(payment_status__in=['unpaid', 'pending']) & ~Q(status='cancelled')),
    )

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
    booking = get_object_or_404(
        Booking,
        Q(id=booking_id) & (Q(user=request.user) | Q(artist__user=request.user))
    )

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
    accounts = dict(settings.PLATFORM_PAYMENT_ACCOUNTS)

    # Override dengan akun artist jika ada
    try:
        ps = booking.artist.payment_settings
        artist_accounts_loaded = True
    except ArtistPaymentSettings.DoesNotExist:
        ps = None
        artist_accounts_loaded = False

    if artist_accounts_loaded and ps:
        # Override bank VA accounts dengan rekening artist
        bank_map = {
            'bca_va': ('bca', 'bank_bca_number', 'bank_bca_name', 'BCA'),
            'mandiri_va': ('mandiri', 'bank_mandiri_number', 'bank_mandiri_name', 'Mandiri'),
            'bni_va': ('bni', 'bank_bni_number', 'bank_bni_name', 'BNI'),
            'bri_va': ('bri', 'bank_bri_number', 'bank_bri_name', 'BRI'),
            'permata_va': ('permata', 'bank_permata_number', 'bank_permata_name', 'Permata'),
            'cimb_va': ('cimb', 'bank_cimb_number', 'bank_cimb_name', 'CIMB Niaga'),
        }
        for method_key, (acct_key, num_field, name_field, default_bank) in bank_map.items():
            acct_num = getattr(ps, num_field, None)
            acct_name = getattr(ps, name_field, None)
            if acct_num and acct_name:
                accounts[acct_key] = {
                    'bank_name': default_bank,
                    'account_number': acct_num,
                    'account_name': acct_name,
                }

        # Override e-wallet accounts dengan nomor artist
        ewallet_map = {
            'gopay': ('ewallet_gopay', 'GoPay'),
            'shopeepay': ('ewallet_shopeepay', 'ShopeePay'),
            'dana': ('ewallet_dana', 'DANA'),
            'ovo': ('ewallet_ovo', 'OVO'),
            'linkaja': ('ewallet_linkaja', 'LinkAja'),
        }
        for method_key, (field, provider) in ewallet_map.items():
            number = getattr(ps, field, None)
            if number:
                accounts[method_key] = {
                    'provider': provider,
                    'number': number,
                    'name': ps.artist.nickname,
                }

    if selected_method and selected_method in METHOD_LABELS:
        # Override khusus credit_card dan qris (sudah ada sebelumnya)
        if selected_method == 'credit_card':
            accounts['credit_card'] = {
                'processing_method': (ps.card_processing_method if ps else 'manual') or 'manual',
                'payment_link': (ps.card_payment_link if ps else '') or '',
                'fee_percent': float(ps.card_fee_percent or 0) if ps else 0,
                'note': (ps.card_note if ps else '') or '',
            }
        elif selected_method == 'qris':
            accounts['qris'] = {
                'merchant_name': (ps.qris_merchant_name if ps else None) or (booking.artist.nickname if hasattr(booking.artist, 'nickname') else 'Merchant'),
                'image_url': (ps.qris_image.url if ps and ps.qris_image else ''),
                'fee_percent': float(ps.qris_fee_percent or 0) if ps else 0.7,
                'note': (ps.qris_note if ps else '') or '',
            }

        instructions = get_payment_instructions(
            selected_method, booking, accounts
        )

    enabled_data = _get_enabled_methods_for_artist(booking.artist)

    return render(request, 'tattoo/payment_page.html', {
        'booking': booking,
        'instructions': instructions,
        'selected_method': selected_method,
        'selected_brand': selected_brand,
        'enabled_methods': enabled_data,
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
            f'Pembayaran pesanan #{booking.id} ditolak. Customer akan diminta upload bukti baru dan melakukan transaksi ulang.'
        )
    return redirect('artist_booking_detail', booking_id=booking.id)


def _get_enabled_methods_for_artist(artist):
    """Return dict dengan group flags dan list metode individual yang enabled."""
    try:
        s = artist.payment_settings
    except ArtistPaymentSettings.DoesNotExist:
        s = None

    def _flag(field, default):
        return getattr(s, field, default) if s else default

    group_flags = {
        'bank_va': _flag('enable_bank_va', True),
        'ewallet': _flag('enable_ewallet', True),
        'credit_card': _flag('enable_credit_card', False),
        'convenience_store': _flag('enable_convenience_store', True),
        'qris': _flag('enable_qris', False),
    }

    # Build list of individually enabled methods
    enabled_methods = []
    if group_flags['bank_va']:
        if _flag('enable_bca', True):    enabled_methods.append('bca_va')
        if _flag('enable_mandiri', True): enabled_methods.append('mandiri_va')
        if _flag('enable_bni', True):    enabled_methods.append('bni_va')
        if _flag('enable_bri', True):    enabled_methods.append('bri_va')
        if _flag('enable_permata', False): enabled_methods.append('permata_va')
        if _flag('enable_cimb', False):  enabled_methods.append('cimb_va')
    if group_flags['ewallet']:
        if _flag('enable_gopay', True):     enabled_methods.append('gopay')
        if _flag('enable_shopeepay', True): enabled_methods.append('shopeepay')
        if _flag('enable_dana', True):      enabled_methods.append('dana')
        if _flag('enable_ovo', True):       enabled_methods.append('ovo')
        if _flag('enable_linkaja', False):  enabled_methods.append('linkaja')
    if group_flags['qris']:
        enabled_methods.append('qris')
    if group_flags['convenience_store']:
        enabled_methods.extend(['indomaret', 'alfamart'])
    if group_flags['credit_card']:
        enabled_methods.append('credit_card')

    return {
        'groups': group_flags,
        'methods': enabled_methods,
    }


def _get_artist_or_404(user):
    try:
        return user.artist
    except (ObjectDoesNotExist, AttributeError):
        raise PermissionDenied('Anda bukan seorang tattoo artist.')


@login_required
def artist_dashboard(request):
    artist = _get_artist_or_404(request.user)
    bookings_qs = Booking.objects.filter(artist=artist).select_related(
        'user', 'service', 'package'
    )

    status_counts = Booking.objects.filter(artist=artist).aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status='pending')),
        confirmed=Count('id', filter=Q(status='confirmed')),
        in_progress=Count('id', filter=Q(status='in_progress')),
        completed=Count('id', filter=Q(status='completed')),
        cancelled=Count('id', filter=Q(status='cancelled')),
    )
    total_bookings = status_counts['total']
    pending_count = status_counts['pending']
    confirmed_count = status_counts['confirmed']
    in_progress_count = status_counts['in_progress']
    completed_count = status_counts['completed']
    cancelled_count = status_counts['cancelled']

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

    # Jika artist membatalkan booking, reset seluruh data pembayaran
    # agar customer harus transaksi ulang jika ingin pesan lagi
    if new_status == 'cancelled':
        booking.payment_status = 'failed'
        booking.is_paid = False
        booking.paid_at = None
        booking.payment_confirmed_at = None
        booking.transaction_id = None
        booking.payment_expires_at = None
        booking.payment_proof = None
        booking.payment_proof_uploaded_at = None
        if booking.payment_verification_status == 'pending':
            booking.payment_verification_status = 'rejected'
            booking.payment_verification_note = 'Pembayaran dibatalkan karena pesanan dibatalkan oleh artist.'
            booking.payment_verified_at = timezone.now()
            booking.payment_verified_by = request.user

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
    artist = Artist.objects.prefetch_related(
        'artist_styles__style', 'style_expertise'
    ).get(id=artist.id)
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
@require_POST
def artist_settings_styles(request):
    try:
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
            current_ids = set(artist.artist_styles.values_list('style_id', flat=True))
            new_ids = set(s.id for s in styles)

            for old_id in current_ids - new_ids:
                ArtistStyle.objects.filter(artist=artist, style_id=old_id).delete()

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
    except DatabaseError:
        messages.error(request, 'Kesalahan database. Silakan coba lagi.')
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
