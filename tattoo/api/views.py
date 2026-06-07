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
                    if not s.accept_online_payment:
                        methods = []
                    elif enabled_only:
                        methods = [m for m in methods if enabled.get(m['group'], False)]
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
        'name': 'Bali Tattoo Studio API',
        'version': 'v1',
        'endpoints': {
            'categories':     f'{base}categories/',
            'services':       f'{base}services/',
            'artists':        f'{base}artists/',
            'bookings':       f'{base}bookings/',
            'payment_methods': f'{base}payment-methods/',
            'health':         f'{base}health/',
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
