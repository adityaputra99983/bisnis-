"""Management command to clean spam messages from chat."""
# pyright: reportMissingImports=false
# pylint: disable=import-error, no-name-in-module
from django.core.management.base import BaseCommand
from django.utils import timezone
from tattoo.models import ChatMessage
import re


SPAM_PATTERNS = [
    re.compile(r'^komik\s*:', re.IGNORECASE),
    re.compile(r'^[a-z0-9;.\-_]{10,}$', re.IGNORECASE),
    re.compile(r'(https?://\S+){3,}'),
    re.compile(r'[\u0100-\uffff]'),
]


class Command(BaseCommand):
    help = 'Remove spam messages from chat'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--booking-id',
            type=int,
            help='Clean spam only for a specific booking ID',
        )

    def handle(self, *args, **options):
        qs = ChatMessage.objects.all()
        if options['booking_id']:
            qs = qs.filter(booking_id=options['booking_id'])

        spam_messages = []
        for msg in qs:
            for pattern in SPAM_PATTERNS:
                if pattern.search(msg.message):
                    spam_messages.append(msg)
                    break

        if options['dry_run']:
            self.stdout.write(f'Found {len(spam_messages)} spam messages:')
            for msg in spam_messages:
                self.stdout.write(f'  - [{msg.id}] {msg.message[:50]}')
        else:
            deleted_count = 0
            for msg in spam_messages:
                msg.delete()
                deleted_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {deleted_count} spam messages.')
            )
