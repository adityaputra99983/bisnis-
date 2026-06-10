from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.service_list, name='service_list'),
    path('services/<int:service_id>/', views.service_detail, name='service_detail'),
    path('artists/', views.artist_list, name='artist_list'),
    path('artists/<int:artist_id>/', views.artist_detail, name='artist_detail'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('booking/new/', views.booking_create, name='booking_create'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('payment/<int:booking_id>/', views.payment_initiate, name='payment_initiate'),
    path('payment/<int:booking_id>/confirm/', views.payment_confirm, name='payment_confirm'),
    path('payment/<int:booking_id>/verify/', views.payment_verify, name='payment_verify'),
    # Artist dashboard / bisnis
    path('artist/dashboard/', views.artist_dashboard, name='artist_dashboard'),
    path('artist/bookings/', views.artist_booking_list, name='artist_booking_list'),
    path('artist/bookings/<int:booking_id>/', views.artist_booking_detail, name='artist_booking_detail'),
    path('artist/bookings/<int:booking_id>/status/', views.artist_update_status, name='artist_update_status'),
    path('artist/profile/edit/', views.artist_profile_edit, name='artist_profile_edit'),
    path('artist/portfolio/', views.artist_portfolio, name='artist_portfolio'),
    path('artist/portfolio/add/', views.artist_portfolio_add, name='artist_portfolio_add'),
    path('artist/portfolio/<int:portfolio_id>/delete/', views.artist_portfolio_delete, name='artist_portfolio_delete'),
    path('artist/services/', views.artist_services, name='artist_services'),
    path('artist/services/<int:service_id>/toggle/', views.artist_toggle_service, name='artist_toggle_service'),
    path('artist/settings/', views.artist_settings, name='artist_settings'),
    path('artist/settings/specialties/', views.artist_settings_specialties, name='artist_settings_specialties'),
    path('artist/settings/styles/', views.artist_settings_styles, name='artist_settings_styles'),
    path('artist/payment-settings/', views.artist_payment_settings, name='artist_payment_settings'),
]
