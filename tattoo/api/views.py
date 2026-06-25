"""DRF Views untuk tattoo API."""
from datetime import datetime, date
from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, status, permissions, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import (
    ServiceCategory, Service, ServicePackage, Artist, Portfolio,
    Booking, Review,
)
from ..payment import (
    generate_payment_session, get_payment_instructions, mark_booking_as_paid,
    verify_payment_proof, METHOD_LABELS, METHOD_LOGO, method_requires_proof,
    is_payment_expired, expire_payment_if_needed,
)
from .serializers import (
    CategorySerializer, ServiceListSerializer, ServiceDetailSerializer,
    PackageSerializer, ArtistListSerializer, ArtistDetailSerializer,
    PortfolioSerializer, ReviewSerializer, BookingSerializer,
    BookingCreateSerializer, PaymentMethodSerializer,
)


# ============================================================
# Read-only resources (public)
# ============================================================

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/v1/categories/ - list semua kategori aktif."""
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    pagination_class = None


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/v1/services/ - list & detail layanan.

    Filter:
    - ?category=<id>
    - ?popular=true
    - ?search=<keyword>
    - ?ordering=price|name|created_at
    """
    queryset = Service.objects.filter(is_active=True).select_related('category')
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['category', 'is_popular', 'difficulty']
    search_fields = ['name', 'short_desc', 'description']
    ordering_fields = ['price', 'name', 'created_at']
    ordering = ['category__sort_order', 'name']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ServiceDetailSerializer
        return ServiceListSerializer

    @action(detail=True, methods=['get'])
    def packages(self, request, pk=None):
        """GET /api/v1/services/<id>/packages/ - list paket untuk layanan ini."""
        service = self.get_object()
        packages = service.packages.filter(is_active=True)
        return Response(PackageSerializer(packages, many=True).data)


class ArtistViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/v1/artists/ - list & detail artist.

    Filter:
    - ?mode=studio|mobile
    - ?search=<keyword>
    - ?specialty=<service_id>
    """
    queryset = Artist.objects.filter(is_active=True).prefetch_related('specialties', 'portfolios')
    permission_classes = [permissions.AllowAny]
    search_fields = ['nickname', 'name', 'short_bio', 'bio', 'service_area']
    filterset_fields = ['is_available_mobile', 'is_available_studio']
    ordering_fields = ['experience_years', 'name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        qs = super().get_queryset()
        mode = self.request.query_params.get('mode')
        if mode == 'mobile':
            qs = qs.filter(is_available_mobile=True)
        elif mode == 'studio':
            qs = qs.filter(is_available_studio=True)
        specialty = self.request.query_params.get('specialty')
        if specialty and specialty.isdigit():
            qs = qs.filter(specialties__id=int(specialty))
        return qs.distinct()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ArtistDetailSerializer
        return ArtistListSerializer

    @action(detail=True, methods=['get'], url_path='portfolio')
    def portfolio(self, request, pk=None):
        """GET /api/v1/artists/<id>/portfolio/ - list portfolio."""
        artist = self.get_object()
        portfolios = artist.portfolios.all()[:20]
        return Response(PortfolioSerializer(portfolios, many=True, context={'request': request}).data)

    @action(detail=True, methods=['get'], url_path='reviews')
    def reviews(self, request, pk=None):
        """GET /api/v1/artists/<id>/reviews/ - list review."""
        artist = self.get_object()
        reviews = Review.objects.filter(booking__artist=artist).select_related('user', 'booking')[:20]
        return Response(ReviewSerializer(reviews, many=True).data)


# ============================================================
# Booking (auth required)
# ============================================================

class IsBookingOwner(permissions.BasePermission):
    """Customer hanya bisa akses booking miliknya; artist hanya booking untuk mereka."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if obj.user_id == request.user.id:
            return True
        # artist owner
        if hasattr(request.user, 'artist') and obj.artist_id == request.user.artist.id:
            return True
        return False


class BookingViewSet(viewsets.ModelViewSet):
    """Booking management.

    GET    /api/v1/bookings/        - list booking user (atau semua untuk artist)
    POST   /api/v1/bookings/        - buat booking baru
    GET    /api/v1/bookings/<id>/   - detail booking
    PATCH  /api/v1/bookings/<id>/   - update (partial)
    DELETE /api/v1/bookings/<id>/   - cancel booking (set status='cancelled')
    """
    permission_classes = [permissions.IsAuthenticated, IsBookingOwner]
    filterset_fields = ['status', 'payment_status', 'mode']
    ordering_fields = ['booking_date', 'created_at', 'total_price']
    ordering = ['-booking_date', '-booking_time']

    def get_queryset(self):
        user = self.request.user
        qs = Booking.objects.select_related('service', 'artist', 'package', 'user')
        if user.is_staff:
            return qs
        # Customer: hanya miliknya
        if hasattr(user, 'artist'):
            return qs.filter(Q(user=user) | Q(artist=user.artist))
        return qs.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingSerializer

    def create(self, request, *args, **kwargs):
        """Create booking lalu return dengan BookingSerializer (full representation)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        full = BookingSerializer(serializer.instance, context={'request': request})
        headers = self.get_success_headers(serializer.data)
        return Response(full.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        service = serializer.validated_data['service']
        package = serializer.validated_data.get('package')
        artist = serializer.validated_data['artist']
        mode = serializer.validated_data.get('mode', 'studio')

        # Hitung total_price dulu (kolom NOT NULL)
        if package:
            total_price = package.price
        else:
            total_price = service.price
        travel_fee = 0
        if mode == 'mobile':
            travel_fee = artist.mobile_fee
            total_price += artist.mobile_fee

        booking = serializer.save(
            user=self.request.user,
            total_price=total_price,
            travel_fee=travel_fee,
        )

    def destroy(self, request, *args, **kwargs):
        booking = self.get_object()
        if booking.status not in ('pending', 'confirmed'):
            return Response(
                {'detail': f'Tidak bisa membatalkan booking berstatus {booking.status}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        booking.status = 'cancelled'

        # Reset seluruh data pembayaran agar customer harus transaksi ulang
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
            booking.payment_verification_note = 'Pembayaran dibatalkan karena pesanan dibatalkan.'
            booking.payment_verified_at = timezone.now()
            booking.payment_verified_by = request.user

        booking.save()
        return Response({'detail': 'Booking dibatalkan.'}, status=status.HTTP_200_OK)

    # ---------- Custom actions ----------

    @action(detail=True, methods=['get'], url_path='payment-instructions')
    def payment_instructions(self, request, pk=None):
        """GET /api/v1/bookings/<id>/payment-instructions/?method=<code>"""
        booking = self.get_object()

        if booking.payment_status == 'paid':
            return Response({'detail': 'Booking sudah lunas.'}, status=400)

        if expire_payment_if_needed(booking):
            return Response({'detail': 'Batas waktu pembayaran sudah habis.'}, status=400)

        method = request.query_params.get('method', '').strip()
        if not method or method not in METHOD_LABELS:
            return Response(
                {'detail': f'Parameter ?method=<code> wajib. Pilihan: {", ".join(METHOD_LABELS.keys())}'},
                status=400
            )

        from django.conf import settings as dj_settings
        accounts = dict(dj_settings.PLATFORM_PAYMENT_ACCOUNTS)

        # Inject artist-specific config
        try:
            ps = booking.artist.payment_settings
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

            accounts['credit_card'] = {
                'processing_method': ps.card_processing_method or 'manual',
                'payment_link': ps.card_payment_link or '',
                'fee_percent': float(ps.card_fee_percent or 0),
                'note': ps.card_note or '',
            }
            accounts['qris'] = {
                'merchant_name': ps.qris_merchant_name or ps.artist.nickname,
                'image_url': ps.qris_image.url if ps.qris_image else '',
                'fee_percent': float(ps.qris_fee_percent or 0),
                'note': ps.qris_note or '',
            }
        except Exception:
            pass

        generate_payment_session(booking)
        booking.refresh_from_db()
        instr = get_payment_instructions(method, booking, accounts)
        if not instr:
            return Response({'detail': 'Metode tidak tersedia.'}, status=400)

        instr['amount'] = int(booking.total_price)
        instr['transaction_id'] = booking.transaction_id
        instr['expires_at'] = booking.payment_expires_at
        return Response(instr)

    @action(detail=True, methods=['post'], url_path='confirm-payment')
    def confirm_payment(self, request, pk=None):
        """POST /api/v1/bookings/<id>/confirm-payment/

        Body (multipart/form-data atau JSON):
        {
            "method": "indomaret",
            "payment_proof": <file>,   # wajib untuk metode yang requires_proof
            "sop_agreement": "1"        # wajib centang SOP
        }
        """
        booking = self.get_object()

        if booking.payment_status == 'paid':
            return Response({'detail': 'Booking sudah lunas.'}, status=400)
        if booking.status == 'cancelled':
            return Response({'detail': 'Booking dibatalkan.'}, status=400)
        if is_payment_expired(booking):
            expire_payment_if_needed(booking)
            return Response({'detail': 'Batas waktu pembayaran habis.'}, status=400)

        method = (request.data.get('method') or '').strip()
        requires_proof = method_requires_proof(method)
        proof_file = request.FILES.get('payment_proof') if requires_proof else None

        if requires_proof and not proof_file:
            return Response(
                {'detail': 'Bukti pembayaran wajib diupload untuk metode ini.'},
                status=400
            )
        if requires_proof:
            allowed = {'image/jpeg', 'image/jpg', 'image/png', 'image/webp'}
            if proof_file.content_type not in allowed:
                return Response({'detail': 'Format harus JPG/PNG/WEBP.'}, status=400)
            if proof_file.size > 5 * 1024 * 1024:
                return Response({'detail': 'Ukuran bukti maks 5 MB.'}, status=400)
        if requires_proof and str(request.data.get('sop_agreement', '')) != '1':
            return Response(
                {'detail': 'Wajib menyetujui pernyataan SOP (sop_agreement=1).'},
                status=400
            )

        success, error = mark_booking_as_paid(booking, method, proof_file=proof_file)
        if not success:
            return Response({'detail': error}, status=400)

        booking.refresh_from_db()
        return Response({
            'detail': 'Bukti pembayaran dikirim. Menunggu verifikasi artist.' if requires_proof
                     else 'Pembayaran berhasil. Booking dikonfirmasi.',
            'booking': BookingSerializer(booking, context={'request': request}).data,
            'requires_verification': requires_proof,
        })

    @action(detail=True, methods=['post'], url_path='verify-payment')
    def verify_payment(self, request, pk=None):
        """POST /api/v1/bookings/<id>/verify-payment/

        Artist approve / reject bukti pembayaran customer.

        Body (JSON):
        {
            "action": "approve" | "reject",
            "note": "alasan penolakan (wajib untuk reject)"
        }
        """
        booking = self.get_object()

        # Hanya artist yang memiliki booking atau staff yang bisa verifikasi
        if not request.user.is_staff:
            if not hasattr(request.user, 'artist') or booking.artist_id != request.user.artist.id:
                return Response(
                    {'detail': 'Kamu tidak memiliki akses untuk memverifikasi pesanan ini.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        if booking.payment_status == 'paid':
            return Response(
                {'detail': 'Pembayaran ini sudah lunas.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        action = (request.data.get('action') or '').strip().lower()
        note = (request.data.get('note') or '').strip()

        success, error = verify_payment_proof(booking, action, note, by=request.user)
        if not success:
            return Response(
                {'detail': error or 'Gagal memproses verifikasi.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.refresh_from_db()
        return Response({
            'detail': 'Pembayaran disetujui. Booking dikonfirmasi.' if action == 'approve'
                     else 'Pembayaran ditolak. Customer akan diminta upload bukti baru dan melakukan transaksi ulang.',
            'booking': BookingSerializer(booking, context={'request': request}).data,
        })


# ============================================================
# Payment Methods (public)
# ============================================================

class PaymentMethodsView(APIView):
    """GET /api/v1/payment-methods/ - list semua metode pembayaran yang tersedia.

    Otomatis filter sesuai setting artist & metode yang enabled.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        artist_id = request.query_params.get('artist_id')
        enabled_only = request.query_params.get('enabled_only', 'false').lower() == 'true'

        methods = []
        groups = {}
        for code, info in METHOD_LABELS.items():
            methods.append({
                'code': code,
                'name': info['name_id'],
                'group': info['group'],
                'logo': METHOD_LOGO.get(code),
                'requires_proof': method_requires_proof(code),
            })
            groups.setdefault(info['group'], []).append(code)

        # Filter by artist
        if artist_id and artist_id.isdigit():
            try:
                artist = Artist.objects.get(id=int(artist_id), is_active=True)
                try:
                    s = artist.payment_settings
                    enabled = {
                        'bank_va': s.enable_bank_va,
                        'ewallet': s.enable_ewallet,
                        'credit_card': s.enable_credit_card,
                        'convenience_store': s.enable_convenience_store,
                        'retail': s.enable_convenience_store,
                        'qris': getattr(s, 'enable_qris', False),
                    }
                    # Per-method enable flags
                    per_method_enabled = set()
                    if enabled.get('bank_va'):
                        if getattr(s, 'enable_bca', True):    per_method_enabled.add('bca_va')
                        if getattr(s, 'enable_mandiri', True): per_method_enabled.add('mandiri_va')
                        if getattr(s, 'enable_bni', True):    per_method_enabled.add('bni_va')
                        if getattr(s, 'enable_bri', True):    per_method_enabled.add('bri_va')
                        if getattr(s, 'enable_permata', False): per_method_enabled.add('permata_va')
                        if getattr(s, 'enable_cimb', False):  per_method_enabled.add('cimb_va')
                    if enabled.get('ewallet'):
                        if getattr(s, 'enable_gopay', True):     per_method_enabled.add('gopay')
                        if getattr(s, 'enable_shopeepay', True): per_method_enabled.add('shopeepay')
                        if getattr(s, 'enable_dana', True):      per_method_enabled.add('dana')
                        if getattr(s, 'enable_ovo', True):       per_method_enabled.add('ovo')
                        if getattr(s, 'enable_linkaja', False):  per_method_enabled.add('linkaja')
                    if enabled.get('qris'):
                        per_method_enabled.add('qris')
                    if enabled.get('convenience_store'):
                        per_method_enabled.update(['indomaret', 'alfamart'])
                    if enabled.get('credit_card'):
                        per_method_enabled.add('credit_card')

                    if not s.accept_online_payment:
                        methods = []
                    elif enabled_only:
                        methods = [m for m in methods if m['code'] in per_method_enabled]
                except Exception:
                    pass
            except Artist.DoesNotExist:
                pass

        return Response({
            'methods': methods,
            'groups': groups,
            'groups_label': {
                'bank_va': 'Virtual Account Bank',
                'ewallet': 'E-Wallet',
                'retail': 'Convenience Store',
                'credit_card': 'Kartu Kredit / Debit',
                'qris': 'QRIS',
            },
        })


# ============================================================
# API root & info endpoints
# ============================================================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_root(request):
    """GET /api/v1/ - root endpoint dengan daftar semua endpoint."""
    base = request.build_absolute_uri('/api/v1/')
    return Response({
        'name': 'Bali Ink Hub API',
        'version': 'v1',
        'endpoints': {
            'categories':     f'{base}categories/',
            'services':       f'{base}services/',
            'artists':        f'{base}artists/',
            'bookings':       f'{base}bookings/',
            'payment_methods': f'{base}payment-methods/',
            'health':         f'{base}health/',
            'diagnose':       f'{base}diagnose/',
        },
        'auth': {
            'session': 'Login di /login/ lalu gunakan cookie session untuk request berikutnya.',
            'basic': 'Header: Authorization: Basic base64(username:password)',
        },
        'docs': 'Lihat DEPLOYMENT.md dan /api/v1/ untuk dokumentasi lengkap.',
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """GET /api/v1/health/ - health check untuk monitoring / load balancer."""
    return Response({
        'status': 'ok',
        'timestamp': timezone.now().isoformat(),
        'service': 'bali-tattoo-api',
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def diagnose(request):
    """GET /api/v1/diagnose/ - diagnostic config (tidak butuh DB connection).

    Berguna untuk debug deployment error tanpa harus bisa konek ke database.
    Menampilkan status env vars, database engine, allowed hosts, dll.
    """
    from django.conf import settings
    import os
    import sys

    # Detect env vars (hanya nama, jangan expose value!)
    supabase_keys = ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'SUPABASE_STORAGE_BUCKET', 'SUPABASE_REGION']
    env_status = {
        'SECRET_KEY': 'SET' if os.environ.get('SECRET_KEY') else 'MISSING',
        'DEBUG': 'True' if settings.DEBUG else 'False',
        'DATABASE_URL': 'SET' if os.environ.get('DATABASE_URL') else 'MISSING',
        'ALLOWED_HOSTS': settings.ALLOWED_HOSTS,
        'CSRF_TRUSTED_ORIGINS': settings.CSRF_TRUSTED_ORIGINS,
        'VERCEL': '1' if os.environ.get('VERCEL') else 'NOT SET',
        'VERCEL_ENV': os.environ.get('VERCEL_ENV', 'NOT SET'),
        'VERCEL_URL': os.environ.get('VERCEL_URL', 'NOT SET'),
    }
    for k in supabase_keys:
        env_status[k] = 'SET' if os.environ.get(k) else 'MISSING'

    # Detect database engine
    db_engine = settings.DATABASES.get('default', {}).get('ENGINE', 'unknown')
    db_name = settings.DATABASES.get('default', {}).get('NAME', 'unknown')
    db_host = settings.DATABASES.get('default', {}).get('HOST', 'N/A')

    # Check common issues
    issues = []
    if not os.environ.get('DATABASE_URL') and os.environ.get('VERCEL'):
        issues.append({
            'severity': 'critical',
            'issue': 'DATABASE_URL tidak di-set di Vercel',
            'fix': 'Set DATABASE_URL di Vercel project settings (Supabase/Neon/Railway PostgreSQL connection string)',
        })
    if db_engine == 'django.db.backends.sqlite3' and os.environ.get('VERCEL'):
        issues.append({
            'severity': 'critical',
            'issue': 'SQLite di Vercel (filesystem read-only)',
            'fix': 'DATABASE_URL harus di-set ke PostgreSQL. Lihat hint di halaman error.',
        })
    if not os.environ.get('SECRET_KEY'):
        issues.append({
            'severity': 'high',
            'issue': 'SECRET_KEY tidak di-set',
            'fix': 'Generate: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"',
        })

    return Response({
        'status': 'diagnostic_ok',
        'service': 'bali-tattoo-api',
        'python_version': sys.version,
        'django_version': __import__('django').VERSION,
        'environment': env_status,
        'database': {
            'engine': db_engine,
            'name': str(db_name),
            'host': str(db_host),
        },
        'static_files': {
            'whitenoise_enabled': any('whitenoise' in m.lower() for m in settings.MIDDLEWARE),
            'static_url': settings.STATIC_URL,
        },
        'issues': issues,
        'next_steps': [
            'GET /api/v1/health/  → basic health check',
            'GET /api/v1/services/  → test DB query',
            'GET /api/v1/diagnose/  → detailed config (this endpoint)',
        ] if not issues else ['Fix issues di atas lalu redeploy Vercel'],
    })


# ============================================================
# Review
# ============================================================

class ReviewViewSet(mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    """Review untuk booking yang sudah selesai.

    POST /api/v1/reviews/ - buat review (harus login & booking milik sendiri & status=completed)
    """
    queryset = Review.objects.all().select_related('user', 'booking')
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['rating']

    def perform_create(self, serializer):
        booking_id = self.request.data.get('booking')
        booking = get_object_or_404(Booking, id=booking_id, user=self.request.user)
        if booking.status != 'completed':
            raise serializers.ValidationError(
                {'booking': 'Hanya booking yang sudah selesai yang bisa direview.'}
            )
        if hasattr(booking, 'review'):
            raise serializers.ValidationError(
                {'booking': 'Booking ini sudah pernah direview.'}
            )
        serializer.save(user=self.request.user, booking=booking)
