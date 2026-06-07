"""DRF Serializers untuk tattoo API."""
from rest_framework import serializers
from ..models import (
    ServiceCategory, Service, ServicePackage, Artist, Portfolio,
    Booking, Review, ArtistPaymentSettings,
)
from ..payment import METHOD_LABELS, method_requires_proof


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'description', 'icon', 'sort_order', 'is_active']


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicePackage
        fields = ['id', 'name', 'description', 'price', 'duration', 'is_recommended', 'is_active']


class ServiceListSerializer(serializers.ModelSerializer):
    """Serializer ringan untuk list services."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            'id', 'name', 'short_desc', 'price', 'price_label',
            'duration', 'difficulty', 'is_popular',
            'category', 'category_name', 'image_url',
        ]

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ServiceDetailSerializer(serializers.ModelSerializer):
    """Serializer lengkap dengan packages."""
    category = CategorySerializer(read_only=True)
    packages = PackageSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'short_desc',
            'price', 'price_label', 'duration', 'difficulty',
            'is_popular', 'is_active',
            'category', 'packages', 'image_url',
            'created_at',
        ]

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ['id', 'title', 'description', 'image', 'service', 'created_at']


class ArtistListSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    specialties = ServiceListSerializer(many=True, read_only=True)
    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    portfolio_count = serializers.SerializerMethodField()

    class Meta:
        model = Artist
        fields = [
            'id', 'nickname', 'name', 'short_bio', 'experience_years',
            'photo_url', 'service_area', 'mobile_fee',
            'is_available_mobile', 'is_available_studio',
            'specialties', 'avg_rating', 'review_count', 'portfolio_count',
            'instagram',
        ]

    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None

    def get_avg_rating(self, obj):
        from django.db.models import Avg
        result = obj.bookings.filter(review__isnull=False).aggregate(
            avg=Avg('review__rating')
        )['avg']
        return round(result, 1) if result else None

    def get_review_count(self, obj):
        return obj.bookings.filter(review__isnull=False).count()

    def get_portfolio_count(self, obj):
        return obj.portfolios.count()


class ArtistDetailSerializer(ArtistListSerializer):
    bio = serializers.CharField(read_only=True)
    portfolios = PortfolioSerializer(many=True, read_only=True)

    class Meta(ArtistListSerializer.Meta):
        fields = ArtistListSerializer.Meta.fields + ['bio', 'portfolios', 'created_at']


class ReviewSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user_username', 'rating', 'comment', 'created_at']
        read_only_fields = ['user_username', 'created_at']


class BookingSerializer(serializers.ModelSerializer):
    """Detail booking lengkap."""
    service_name = serializers.CharField(source='service.name', read_only=True)
    artist_nickname = serializers.CharField(source='artist.nickname', read_only=True)
    artist_name = serializers.CharField(source='artist.name', read_only=True)
    package_name = serializers.CharField(source='package.name', read_only=True, default=None)
    user_username = serializers.CharField(source='user.username', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)
    requires_proof = serializers.SerializerMethodField()
    design_reference_url = serializers.SerializerMethodField()
    payment_proof_url = serializers.SerializerMethodField()
    expires_at = serializers.DateTimeField(read_only=True)
    verification_status = serializers.CharField(source='payment_verification_status', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'transaction_id',
            'user', 'user_username',
            'artist', 'artist_nickname', 'artist_name',
            'service', 'service_name',
            'package', 'package_name',
            'mode', 'mode_display',
            'status', 'status_display',
            'booking_date', 'booking_time',
            'location_address', 'notes',
            'total_price', 'travel_fee',
            'is_paid', 'paid_at',
            'payment_status', 'payment_status_display',
            'payment_method', 'transaction_id',
            'expires_at', 'requires_proof',
            'design_reference_url', 'payment_proof_url',
            'verification_status',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'user', 'transaction_id', 'is_paid', 'paid_at',
            'payment_status', 'payment_method', 'expires_at',
            'verification_status', 'created_at', 'updated_at',
        ]

    def get_requires_proof(self, obj):
        if obj.payment_method:
            # cari method code by label
            for code, info in METHOD_LABELS.items():
                if info['name_id'] == obj.payment_method:
                    return method_requires_proof(code)
        return False

    def get_design_reference_url(self, obj):
        if obj.design_reference:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.design_reference.url)
            return obj.design_reference.url
        return None

    def get_payment_proof_url(self, obj):
        if obj.payment_proof:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.payment_proof.url)
            return obj.payment_proof.url
        return None


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer untuk membuat booking baru via API."""

    class Meta:
        model = Booking
        fields = [
            'artist', 'service', 'package',
            'mode', 'booking_date', 'booking_time',
            'location_address', 'notes', 'design_reference',
        ]

    def validate(self, data):
        artist = data.get('artist')
        service = data.get('service')
        package = data.get('package')
        mode = data.get('mode', 'studio')

        if not artist or not artist.is_active:
            raise serializers.ValidationError({'artist': 'Artist tidak aktif.'})

        if service not in artist.specialties.all() and not service.is_popular:
            raise serializers.ValidationError(
                {'service': f'Artist {artist.nickname} tidak melayani {service.name}.'}
            )

        if package and package.service_id != service.id:
            raise serializers.ValidationError(
                {'package': 'Paket tidak sesuai dengan layanan.'}
            )

        if mode == 'mobile' and not artist.is_available_mobile:
            raise serializers.ValidationError(
                {'mode': f'{artist.nickname} tidak melayani panggil ke rumah.'}
            )
        if mode == 'studio' and not artist.is_available_studio:
            raise serializers.ValidationError(
                {'mode': f'{artist.nickname} tidak melayani di studio.'}
            )

        return data


class PaymentMethodSerializer(serializers.Serializer):
    """Serializer untuk payment method info."""
    code = serializers.CharField()
    name = serializers.CharField()
    group = serializers.CharField()
    logo = serializers.CharField()
    requires_proof = serializers.BooleanField()


class PaymentMethodsResponseSerializer(serializers.Serializer):
    """Response untuk /api/v1/payment-methods/"""
    methods = PaymentMethodSerializer(many=True)
    groups = serializers.DictField()
