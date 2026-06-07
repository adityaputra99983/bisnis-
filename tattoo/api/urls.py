"""URL routing untuk REST API di /api/v1/."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# DRF router untuk ViewSets
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'services', views.ServiceViewSet, basename='service')
router.register(r'artists', views.ArtistViewSet, basename='artist')
router.register(r'bookings', views.BookingViewSet, basename='booking')
router.register(r'reviews', views.ReviewViewSet, basename='review')


urlpatterns = [
    # Root info
    path('', views.api_root, name='api-root'),

    # Health check
    path('health/', views.health_check, name='api-health'),

    # Payment methods (custom view, bukan ViewSet)
    path('payment-methods/', views.PaymentMethodsView.as_view(), name='api-payment-methods'),

    # Router URLs (categories, services, artists, bookings, reviews)
    path('', include(router.urls)),
]
