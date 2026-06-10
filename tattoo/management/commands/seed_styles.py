from django.core.management.base import BaseCommand
from tattoo.models import Style


STYLES = [
    {'name': 'Old School', 'icon': 'bi-bicycle', 'sort_order': 1},
    {'name': 'Watercolor', 'icon': 'bi-droplet', 'sort_order': 2},
    {'name': 'Fine Line', 'icon': 'bi-pen', 'sort_order': 3},
    {'name': 'Bali Traditional', 'icon': 'bi-flower1', 'sort_order': 4},
    {'name': 'Tribal', 'icon': 'bi-intersect', 'sort_order': 5},
    {'name': 'Geometric', 'icon': 'bi-hexagon', 'sort_order': 6},
    {'name': 'Realism', 'icon': 'bi-camera', 'sort_order': 7},
    {'name': 'Neo Traditional', 'icon': 'bi-brush', 'sort_order': 8},
    {'name': 'Minimalist', 'icon': 'bi-circle', 'sort_order': 9},
    {'name': 'Dotwork', 'icon': 'bi-grid-3x3', 'sort_order': 10},
    {'name': 'Blackwork', 'icon': 'bi-moon', 'sort_order': 11},
    {'name': 'Japanese', 'icon': 'bi-dragon', 'sort_order': 12},
]


class Command(BaseCommand):
    help = 'Seed initial tattoo styles'

    def handle(self, *args, **options):
        created = 0
        for data in STYLES:
            _, is_new = Style.objects.get_or_create(
                name=data['name'],
                defaults=data,
            )
            if is_new:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'  + {data["name"]}'))
            else:
                self.stdout.write(f'  ~ {data["name"]} (already exists)')
        self.stdout.write(self.style.SUCCESS(f'\nDone! {created} new styles created.'))
