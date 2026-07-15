from django.db.models import Q, Count
from django.core.cache import cache
from .models import ServiceCategory, Booking, ChatMessage


_SKIP_PATHS = frozenset([
    '/booking/new', '/booking/new/',
    '/login', '/login/',
    '/register', '/register/',
])


def _is_booking_page(path):
    return path.startswith('/booking/') or path.startswith('/payment/') or path.startswith('/bookings/')


def navbar_data(request):
    path = request.path.rstrip('/') or '/'
    skip_all = path in _SKIP_PATHS or _is_booking_page(path)

    categories = cache.get('nav_categories')
    if categories is None and not skip_all:
        try:
            categories = list(ServiceCategory.objects.filter(is_active=True).only('id', 'name', 'slug')[:6])
            cache.set('nav_categories', categories, 600)
        except Exception:
            categories = []

    user_bookings_count = 0
    user_unpaid_count = 0
    user_active_count = 0
    user_recent_bookings = []
    has_new_activity = False

    artist_obj = None
    nav_artist_pending_count = 0
    nav_chat_unread = 0
    nav_chat_first_id = None
    nav_artist_chat_unread = 0
    nav_artist_chat_first_id = None

    if request.user.is_authenticated and not skip_all:
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
                user_recent_bookings = list(qs.order_by('-created_at')[:3])
                has_new_activity = user_unpaid_count > 0 or user_active_count > 0
            except Exception:
                pass

            try:
                artist_obj = request.user.artist
                nav_artist_pending_count = Booking.objects.filter(
                    artist=artist_obj, status='pending'
                ).only('id').count()
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
            }, 600)

        try:
            if artist_obj is None:
                artist_obj = request.user.artist
            if artist_obj:
                artist_booking_ids = Booking.objects.filter(
                    artist=artist_obj
                ).values_list('id', flat=True)
                artist_unread_qs = ChatMessage.objects.filter(
                    booking_id__in=artist_booking_ids
                ).exclude(sender=request.user).filter(is_read=False)
                nav_artist_chat_unread = artist_unread_qs.count()
                if nav_artist_chat_unread > 0:
                    first_artist_msg = artist_unread_qs.order_by('-created_at').first()
                    nav_artist_chat_first_id = first_artist_msg.booking_id if first_artist_msg else None
        except Exception:
            pass

        chat_cache_key = f'nav_chat_unread_{user_id}'
        nav_chat_unread = cache.get(chat_cache_key)
        nav_chat_first_id = cache.get(f'nav_chat_first_{user_id}')
        if nav_chat_unread is None:
            try:
                user_booking_ids = Booking.objects.filter(
                    Q(user=request.user) | Q(artist__user=request.user)
                ).values_list('id', flat=True)
                unread_qs = ChatMessage.objects.filter(
                    booking_id__in=user_booking_ids
                ).exclude(sender=request.user).filter(is_read=False)
                nav_chat_unread = unread_qs.count()
                if nav_chat_unread > 0:
                    first_msg = unread_qs.order_by('-created_at').first()
                    nav_chat_first_id = first_msg.booking_id if first_msg else None
                else:
                    nav_chat_first_id = None
            except Exception:
                nav_chat_unread = 0
                nav_chat_first_id = None
            cache.set(chat_cache_key, nav_chat_unread, 30)
            cache.set(f'nav_chat_first_{user_id}', nav_chat_first_id, 30)

    return {
        'nav_categories': categories,
        'nav_user_bookings_count': user_bookings_count,
        'nav_user_unpaid_count': user_unpaid_count,
        'nav_user_active_count': user_active_count,
        'nav_user_recent_bookings': user_recent_bookings,
        'nav_has_new_activity': has_new_activity,
        'nav_artist_obj': artist_obj,
        'nav_artist_pending_count': nav_artist_pending_count,
        'nav_chat_unread': nav_chat_unread,
        'nav_chat_first_id': nav_chat_first_id,
        'nav_artist_chat_unread': nav_artist_chat_unread,
        'nav_artist_chat_first_id': nav_artist_chat_first_id,
    }
