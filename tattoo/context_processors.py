from django.db.models import Q, Count
from django.core.cache import cache
from .models import ServiceCategory, Booking, Artist


def navbar_data(request):
    categories = cache.get('nav_categories')
    if categories is None:
        try:
            categories = list(ServiceCategory.objects.filter(is_active=True)[:6])
            cache.set('nav_categories', categories, 300)
        except Exception:
            categories = []

    user_bookings_count = 0
    user_unpaid_count = 0
    user_active_count = 0
    user_recent_bookings = []
    has_new_activity = False

    artist_obj = None
    nav_artist_pending_count = 0

    if request.user.is_authenticated:
        user_id = request.user.id
        cache_key = f'nav_booking_{user_id}'
        cached = cache.get(cache_key)

        if cached:
            user_bookings_count = cached['total']
            user_unpaid_count = cached['unpaid']
            user_active_count = cached['active']
            user_recent_bookings = cached['recent']
            has_new_activity = cached['has_new']
            artist_obj = cached.get('artist_obj')
            nav_artist_pending_count = cached.get('artist_pending', 0)
        else:
            try:
                qs = Booking.objects.filter(user=request.user).select_related(
                    'artist', 'service'
                )
                counts = qs.aggregate(
                    total=Count('id'),
                    unpaid=Count('id', filter=Q(payment_status__in=['unpaid', 'pending']) & ~Q(status='cancelled')),
                    active=Count('id', filter=Q(status__in=['pending', 'confirmed', 'in_progress'])),
                )
                user_bookings_count = counts['total']
                user_unpaid_count = counts['unpaid']
                user_active_count = counts['active']
                user_recent_bookings = list(qs.order_by('-created_at')[:4])
                has_new_activity = user_unpaid_count > 0 or user_active_count > 0
            except Exception:
                pass

            try:
                artist_obj = request.user.artist
                nav_artist_pending_count = Booking.objects.filter(
                    artist=artist_obj, status='pending'
                ).count()
            except Exception:
                pass

            cache.set(cache_key, {
                'total': user_bookings_count,
                'unpaid': user_unpaid_count,
                'active': user_active_count,
                'recent': user_recent_bookings,
                'has_new': has_new_activity,
                'artist_obj': artist_obj,
                'artist_pending': nav_artist_pending_count,
            }, 300)

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
