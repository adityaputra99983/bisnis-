from django.contrib import admin
from .models import ServiceCategory, Service, ServicePackage, Artist, Portfolio, Booking, Review


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'sort_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']


class ServicePackageInline(admin.TabularInline):
    model = ServicePackage
    extra = 1


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'duration', 'difficulty', 'is_popular', 'is_active']
    list_filter = ['category', 'difficulty', 'is_popular', 'is_active']
    search_fields = ['name', 'description']
    inlines = [ServicePackageInline]


@admin.register(ServicePackage)
class ServicePackageAdmin(admin.ModelAdmin):
    list_display = ['service', 'name', 'price', 'duration', 'is_recommended']
    list_filter = ['is_recommended', 'service__category']


class PortfolioInline(admin.TabularInline):
    model = Portfolio
    extra = 1


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ['name', 'nickname', 'experience_years',
                    'is_available_mobile', 'is_available_studio', 'mobile_fee', 'is_active']
    list_filter = ['is_available_mobile', 'is_available_studio', 'is_active']
    search_fields = ['name', 'nickname', 'bio']
    filter_horizontal = ['specialties']
    inlines = [PortfolioInline]


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['artist', 'title', 'service', 'created_at']
    list_filter = ['artist', 'service']
    search_fields = ['title', 'description']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'artist', 'service', 'package', 'mode',
                    'status', 'booking_date', 'booking_time', 'total_price', 'is_paid']
    list_filter = ['status', 'mode', 'booking_date', 'is_paid']
    search_fields = ['user__username', 'artist__name', 'location_address']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'booking', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['user__username', 'comment']
