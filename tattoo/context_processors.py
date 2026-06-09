from django.core.exceptions import ObjectDoesNotExist
from .models import ServiceCategory, Booking, Artist


def navbar_data(request):
    categories = ServiceCategory.objects.filter(is_active=True)[:6]

    user_bookings_count = 0
    user_unpaid_count = 0
    user_active_count = 0
    user_recent_bookings = []
    has_new_activity = False

    # Artist nav data
    artist_obj = None
    nav_artist_pending_count = 0

    if request.user.is_authenticated:
        qs = Booking.objects.filter(user=request.user).select_related(
            'artist', 'service'
        )
        user_bookings_count = qs.count()
        user_unpaid_count = qs.filter(
            payment_status__in=['unpaid', 'pending']
        ).exclude(status='cancelled').count()
        user_active_count = qs.filter(
            status__in=['pending', 'confirmed', 'in_progress']
        ).count()
        user_recent_bookings = list(qs.order_by('-created_at')[:4])
        has_new_activity = user_unpaid_count > 0 or user_active_count > 0

        # Check if user has an artist profile
        try:
            artist_obj = request.user.artist
            nav_artist_pending_count = Booking.objects.filter(
                artist=artist_obj, status='pending'
            ).count()
        except ObjectDoesNotExist:
            pass

    return {
        'nav_categories': categories,
        'nav_user_bookings_count': user_bookings_count,
        'nav_user_unpaid_count': user_unpaid_count,
        'nav_user_active_count': user_active_count,
        'nav_user_recent_bookings': user_recent_bookings,
        'nav_has_new_activity': has_new_activity,
        'nav_artist_obj': artist_obj,
        'nav_artist_pending_count': nav_artist_pending_count,
    }
