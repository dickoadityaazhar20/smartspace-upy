"""
Background Scheduler for SmartSpace UPY
Runs scheduled tasks automatically when Django starts

Tasks:
- Daily H-1 booking reminder at 07:00 AM
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def send_daily_reminders():
    """Job function to send H-1 reminder emails"""
    from django.utils import timezone
    from datetime import timedelta
    from core.models import Booking
    from core.email_utils import send_booking_reminder_email
    
    logger.info("Running daily reminder job...")
    
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
        logger.info("No bookings found for tomorrow.")
        return
    
    logger.info(f"Found {bookings.count()} bookings for tomorrow.")
    
    success_count = 0
    for booking in bookings:
        try:
            if send_booking_reminder_email(booking):
                success_count += 1
                logger.info(f"Reminder sent to {booking.user.email}")
        except Exception as e:
            logger.error(f"Failed to send reminder to {booking.user.email}: {e}")
    
    logger.info(f"Daily reminder job completed. Sent: {success_count}/{bookings.count()}")


def start_scheduler():
    """Start the background scheduler"""
    global scheduler
    
    if scheduler is not None:
        logger.info("Scheduler already running.")
        return
    
    scheduler = BackgroundScheduler()
    
    # Schedule daily reminder at 07:00 AM
    scheduler.add_job(
        send_daily_reminders,
        trigger=CronTrigger(hour=7, minute=0),
        id='daily_reminder',
        name='Send H-1 booking reminders',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Background scheduler started! H-1 reminders will be sent daily at 07:00 AM")
    print("✅ Background scheduler started! H-1 reminders will be sent daily at 07:00 AM")


def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None
        logger.info("Scheduler stopped.")
