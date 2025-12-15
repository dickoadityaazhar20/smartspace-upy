"""
Django Signals for Activity Logging

Auto-logs create, update, delete actions for tracked models.
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.admin.models import LogEntry
from .models import Room, Booking, Testimonial, Feedback, ActivityLog


def get_client_ip(request):
    """Get client IP from request"""
    if request is None:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_activity(user, action, model_name, object_id, object_repr, changes=None, ip_address=None):
    """Create an activity log entry"""
    ActivityLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        object_repr=str(object_repr)[:200],
        changes=changes or {},
        ip_address=ip_address
    )


# Store pre-save state for detecting changes
_pre_save_instances = {}

@receiver(pre_save, sender=Room)
@receiver(pre_save, sender=Booking)
@receiver(pre_save, sender=Testimonial)
def store_pre_save_instance(sender, instance, **kwargs):
    """Store instance before save to detect changes"""
    if instance.pk:
        try:
            _pre_save_instances[f"{sender.__name__}_{instance.pk}"] = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=Room)
def log_room_save(sender, instance, created, **kwargs):
    """Log Room create/update"""
    action = 'create' if created else 'update'
    changes = {}
    
    if not created:
        key = f"Room_{instance.pk}"
        old_instance = _pre_save_instances.pop(key, None)
        if old_instance:
            for field in ['nomor_ruangan', 'tipe_ruangan', 'kapasitas', 'is_active']:
                old_val = getattr(old_instance, field, None)
                new_val = getattr(instance, field, None)
                if old_val != new_val:
                    changes[field] = {'old': str(old_val), 'new': str(new_val)}
    
    # Note: user tracking requires middleware or explicit passing
    # For now, we log without user (will be enhanced with admin override)
    log_activity(
        user=None,
        action=action,
        model_name='Room',
        object_id=instance.pk,
        object_repr=str(instance),
        changes=changes
    )


@receiver(post_save, sender=Booking)
def log_booking_save(sender, instance, created, **kwargs):
    """Log Booking create/update"""
    action = 'create' if created else 'update'
    changes = {}
    
    if not created:
        key = f"Booking_{instance.pk}"
        old_instance = _pre_save_instances.pop(key, None)
        if old_instance:
            old_status = old_instance.status
            new_status = instance.status
            if old_status != new_status:
                changes['status'] = {'old': old_status, 'new': new_status}
                # Detect approve/reject actions
                if new_status == 'Approved' and old_status != 'Approved':
                    action = 'approve'
                elif new_status == 'Rejected' and old_status != 'Rejected':
                    action = 'reject'
    
    log_activity(
        user=None,
        action=action,
        model_name='Booking',
        object_id=instance.pk,
        object_repr=str(instance),
        changes=changes
    )


@receiver(post_delete, sender=Room)
def log_room_delete(sender, instance, **kwargs):
    """Log Room delete"""
    log_activity(
        user=None,
        action='delete',
        model_name='Room',
        object_id=instance.pk,
        object_repr=str(instance),
    )


@receiver(post_delete, sender=Booking)
def log_booking_delete(sender, instance, **kwargs):
    """Log Booking delete"""
    log_activity(
        user=None,
        action='delete',
        model_name='Booking',
        object_id=instance.pk,
        object_repr=str(instance),
    )
