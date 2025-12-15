"""
Management command to send H-1 reminder emails for upcoming bookings.
Run this command daily (e.g., via cron or Windows Task Scheduler)

Usage:
    python manage.py send_reminders
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Booking
from core.email_utils import send_booking_reminder_email


class Command(BaseCommand):
    help = 'Send H-1 reminder emails for approved bookings happening tomorrow'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Checking for bookings to remind...'))
        
        # Get tomorrow's date range
        now = timezone.now()
        tomorrow_start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_end = tomorrow_start + timedelta(days=1)
        
        # Find approved bookings for tomorrow
        bookings = Booking.objects.filter(
            status='Approved',
            tanggal_mulai__gte=tomorrow_start,
            tanggal_mulai__lt=tomorrow_end
        ).select_related('user', 'room')
        
        if not bookings.exists():
            self.stdout.write(self.style.WARNING('No bookings found for tomorrow.'))
            return
        
        self.stdout.write(f'Found {bookings.count()} bookings for tomorrow.')
        
        success_count = 0
        fail_count = 0
        
        for booking in bookings:
            try:
                if send_booking_reminder_email(booking):
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Reminder sent to {booking.user.email}')
                    )
                else:
                    fail_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Failed to send to {booking.user.email}')
                    )
            except Exception as e:
                fail_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error for {booking.user.email}: {str(e)}')
                )
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✓ Successfully sent: {success_count}'))
        if fail_count > 0:
            self.stdout.write(self.style.ERROR(f'✗ Failed: {fail_count}'))
        self.stdout.write(self.style.NOTICE('Reminder job completed.'))
