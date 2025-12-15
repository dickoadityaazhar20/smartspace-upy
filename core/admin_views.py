"""
Custom Admin Views for WhatsApp-style Chat Interface
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q, Max, Count
from .models import Message, User, PinnedConversation


@staff_member_required
def admin_shortcuts_view(request):
    """Display keyboard shortcuts guide"""
    shortcuts = [
        {'key': 'S', 'action': 'Sidebar Search', 'description': 'Fokus ke pencarian di sidebar (kiri)'},
        {'key': '/', 'action': 'Table Search', 'description': 'Fokus ke pencarian tabel (kanan)'},
        {'key': 'D', 'action': 'Dashboard', 'description': 'Navigasi ke Dashboard'},
        {'key': 'U', 'action': 'Users', 'description': 'Navigasi ke halaman Users'},
        {'key': 'R', 'action': 'Ruangan', 'description': 'Navigasi ke halaman Ruangan'},
        {'key': 'P', 'action': 'Peminjaman', 'description': 'Navigasi ke halaman Peminjaman'},
        {'key': 'W', 'action': 'Wishlist', 'description': 'Navigasi ke halaman Wishlist'},
        {'key': 'C', 'action': 'Chat User', 'description': 'Navigasi ke halaman Chat'},
        {'key': 'T', 'action': 'Testimoni', 'description': 'Navigasi ke halaman Testimoni'},
        {'key': 'A', 'action': 'Admin Shortcut', 'description': 'Navigasi ke halaman ini'},
    ]
    return render(request, 'admin/core/shortcuts_guide.html', {
        'shortcuts': shortcuts,
        'title': 'Admin Keyboard Shortcuts'
    })


@staff_member_required
def chat_list_view(request):
    """Show list of conversations with users"""
    admin_user = request.user
    filter_type = request.GET.get('filter', 'all')  # all, unread, pinned
    
    # Get all users who have messaged or been messaged by admin
    users_with_messages = User.objects.filter(
        Q(sent_messages__receiver=admin_user) | 
        Q(received_messages__sender=admin_user)
    ).distinct().exclude(is_superuser=True).exclude(role='Admin')
    
    # Get pinned users for this admin
    pinned_user_ids = set(
        PinnedConversation.objects.filter(admin=admin_user).values_list('user_id', flat=True)
    )
    
    conversations = []
    total_unread = 0
    
    for user in users_with_messages:
        # Get last message in conversation
        last_message = Message.objects.filter(
            Q(sender=user, receiver=admin_user) |
            Q(sender=admin_user, receiver=user)
        ).order_by('-created_at').first()
        
        # Count unread messages from this user
        unread_count = Message.objects.filter(
            sender=user,
            receiver=admin_user,
            is_read=False
        ).count()
        
        total_unread += unread_count
        is_pinned = user.id in pinned_user_ids
        
        # Apply filters
        if filter_type == 'unread' and unread_count == 0:
            continue
        if filter_type == 'pinned' and not is_pinned:
            continue
        
        if last_message:
            # Pre-compute display values to avoid complex template tags
            display_name = user.get_full_name() or user.username
            initial = (user.first_name[0].upper() if user.first_name else user.username[0].upper())
            
            conversations.append({
                'user': user,
                'user_display_name': display_name,
                'user_initial': initial,
                'last_message': last_message,
                'unread_count': unread_count,
                'is_pinned': is_pinned
            })
    
    # Sort: pinned first, then by last message time
    conversations.sort(key=lambda x: (not x['is_pinned'], -x['last_message'].created_at.timestamp()))
    
    return render(request, 'admin/core/message_conversations.html', {
        'conversations': conversations,
        'total_unread': total_unread,
        'current_filter': filter_type,
        'title': 'Chat dengan User'
    })


@staff_member_required
def chat_detail_view(request, user_id):
    """Show chat with specific user"""
    admin_user = request.user
    chat_user = get_object_or_404(User, pk=user_id)
    
    # Get all messages between admin and this user
    messages_list = Message.objects.filter(
        Q(sender=chat_user, receiver=admin_user) |
        Q(sender=admin_user, receiver=chat_user)
    ).select_related('sender', 'receiver').order_by('created_at')
    
    # Mark all messages from user as read (auto-read when entering chat)
    Message.objects.filter(
        sender=chat_user,
        receiver=admin_user,
        is_read=False
    ).update(is_read=True)
    
    # Pre-compute display values
    display_name = chat_user.get_full_name() or chat_user.username
    initial = chat_user.first_name[0].upper() if chat_user.first_name else chat_user.username[0].upper()
    
    return render(request, 'admin/core/message_chat.html', {
        'chat_user': chat_user,
        'user_display_name': display_name,
        'user_initial': initial,
        'messages_list': messages_list,
        'title': f'Chat dengan {display_name}'
    })


@staff_member_required
@csrf_protect
def chat_send_view(request):
    """Send message to user from admin"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        receiver_id = request.POST.get('receiver_id')
        content = request.POST.get('content', '').strip()
        attachment = request.FILES.get('attachment')
        
        if not receiver_id:
            return JsonResponse({'success': False, 'message': 'Receiver ID required'}, status=400)
        
        if not content and not attachment:
            return JsonResponse({'success': False, 'message': 'Pesan atau lampiran wajib diisi'}, status=400)
        
        receiver = get_object_or_404(User, pk=receiver_id)
        
        # Create message
        message = Message.objects.create(
            sender=request.user,
            receiver=receiver,
            content=content or 'Mengirim lampiran',
            message_type='admin_to_user',
            attachment=attachment,
            is_read=False
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Pesan terkirim',
            'message_id': message.id,
            'data': {
                'id': message.id,
                'content': message.content,
                'created_at': message.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_member_required
@csrf_protect
def chat_delete_view(request):
    """Delete a message"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        message_id = data.get('message_id')
        
        if not message_id:
            return JsonResponse({'success': False, 'message': 'Message ID required'}, status=400)
        
        message = get_object_or_404(Message, pk=message_id)
        
        # Only allow deleting messages in conversations with admin
        admin_user = request.user
        if message.sender != admin_user and message.receiver != admin_user:
            return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
        
        message.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Pesan berhasil dihapus'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_member_required
@csrf_protect
def chat_delete_conversation_view(request):
    """Delete all messages in a conversation with a user"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        if not user_id:
            return JsonResponse({'success': False, 'message': 'User ID required'}, status=400)
        
        admin_user = request.user
        target_user = get_object_or_404(User, pk=user_id)
        
        # Delete all messages between admin and target user
        deleted_count, _ = Message.objects.filter(
            Q(sender=target_user, receiver=admin_user) |
            Q(sender=admin_user, receiver=target_user)
        ).delete()
        
        return JsonResponse({
            'success': True,
            'message': f'{deleted_count} pesan berhasil dihapus',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_member_required
def chat_poll_view(request, user_id):
    """Poll for new messages - returns messages after a given timestamp"""
    from django.utils import timezone
    from datetime import datetime
    
    admin_user = request.user
    chat_user = get_object_or_404(User, pk=user_id)
    
    # Get last_id from query params
    last_id = request.GET.get('last_id', 0)
    try:
        last_id = int(last_id)
    except:
        last_id = 0
    
    # Get messages newer than last_id
    messages = Message.objects.filter(
        Q(sender=chat_user, receiver=admin_user) |
        Q(sender=admin_user, receiver=chat_user)
    ).filter(id__gt=last_id).select_related('sender').order_by('created_at')
    
    # Mark incoming messages as read
    Message.objects.filter(
        sender=chat_user,
        receiver=admin_user,
        is_read=False
    ).update(is_read=True)
    
    # Build response
    messages_data = []
    for msg in messages:
        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'sender_id': msg.sender.id,
            'is_admin': msg.sender == admin_user,
            'time': msg.created_at.strftime('%H:%M'),
            'attachment_url': msg.attachment.url if msg.attachment else None,
            'is_image': msg.is_image if hasattr(msg, 'is_image') else False
        })
    
    return JsonResponse({
        'success': True,
        'messages': messages_data,
        'count': len(messages_data)
    })


@staff_member_required
@csrf_protect
def chat_pin_view(request):
    """Toggle pin status for a conversation"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        if not user_id:
            return JsonResponse({'success': False, 'message': 'User ID required'}, status=400)
        
        admin_user = request.user
        target_user = get_object_or_404(User, pk=user_id)
        
        # Toggle pin status
        pin, created = PinnedConversation.objects.get_or_create(
            admin=admin_user,
            user=target_user
        )
        
        if not created:
            # Already pinned, so unpin
            pin.delete()
            return JsonResponse({
                'success': True,
                'is_pinned': False,
                'message': 'Percakapan berhasil di-unpin'
            })
        
        return JsonResponse({
            'success': True,
            'is_pinned': True,
            'message': 'Percakapan berhasil di-pin'
        })
        

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_member_required
def admin_dashboard_stats(request):
    """API view to provide statistics for the Admin Dashboard"""
    from django.db.models.functions import TruncDate, ExtractWeekDay
    from django.utils import timezone
    from datetime import timedelta
    from django.core.serializers.json import DjangoJSONEncoder
    from .models import Booking, Room 
    
    # 1. Scorecards Data
    total_bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status='Pending').count()
    approved_bookings = Booking.objects.filter(status='Approved').count()
    active_rooms = Room.objects.filter(is_active=True).count()
    
    # 2. Status Distribution (Pie Chart)
    # Returns list of dicts: [{'status': 'Approved', 'count': 5}, ...]
    status_counts = list(Booking.objects.values('status').annotate(count=Count('status')))
    
    # 3. Bookings Last 30 Days (Line Chart)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_bookings_raw = list(
        Booking.objects.filter(created_at__gte=thirty_days_ago)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    # Convert date objects to ISO format strings for JSON serialization
    daily_bookings = [
        {'date': item['date'].isoformat() if item['date'] else None, 'count': item['count']}
        for item in daily_bookings_raw
    ]
    
    # 4. Popular Days (Bar Chart)
    # week_day: 1 (Sunday) to 7 (Saturday)
    weekly_bookings = list(
        Booking.objects.annotate(day=ExtractWeekDay('tanggal_mulai'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    
    return JsonResponse({
        'success': True,
        'summary': {
            'total': total_bookings,
            'pending': pending_bookings,
            'approved': approved_bookings,
            'active_rooms': active_rooms
        },
        'status_distribution': status_counts,
        'daily_trend': daily_bookings,
        'weekly_popularity': weekly_bookings
    }, encoder=DjangoJSONEncoder)


# ============================================
# EXPORT ENDPOINTS
# ============================================

@staff_member_required
def export_users_excel(request):
    """Export users list to Excel"""
    from .export_utils import generate_users_excel
    users = User.objects.all().order_by('-date_joined')
    return generate_users_excel(users)


@staff_member_required
def export_bookings_excel(request):
    """Export bookings list to Excel"""
    from .export_utils import generate_bookings_excel
    from .models import Booking
    bookings = Booking.objects.select_related('user', 'room').order_by('-created_at')
    return generate_bookings_excel(bookings)


@staff_member_required
def export_bookings_pdf(request):
    """Export bookings list to PDF"""
    from .export_utils import generate_bookings_pdf
    from .models import Booking
    bookings = Booking.objects.select_related('user', 'room').order_by('-created_at')
    return generate_bookings_pdf(bookings)


@staff_member_required
def export_dashboard_excel(request):
    """Export dashboard report to Excel"""
    from .export_utils import generate_dashboard_excel
    from .models import Room, Booking
    from django.db.models import Count
    
    stats = {
        'summary': {
            'total': Booking.objects.count(),
            'pending': Booking.objects.filter(status='Pending').count(),
            'approved': Booking.objects.filter(status='Approved').count(),
            'active_rooms': Room.objects.filter(is_active=True).count(),
        },
        'status_distribution': list(
            Booking.objects.values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
    }
    return generate_dashboard_excel(stats)


@staff_member_required
def export_dashboard_pdf(request):
    """Export dashboard report to PDF"""
    from .export_utils import generate_dashboard_pdf
    from .models import Room, Booking
    from django.db.models import Count
    
    stats = {
        'summary': {
            'total': Booking.objects.count(),
            'pending': Booking.objects.filter(status='Pending').count(),
            'approved': Booking.objects.filter(status='Approved').count(),
            'active_rooms': Room.objects.filter(is_active=True).count(),
        },
        'status_distribution': list(
            Booking.objects.values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
    }
    return generate_dashboard_pdf(stats)


# ============================================
# ADMIN NOTIFICATION BADGE
# ============================================

def get_pending_booking_count(request):
    """Get count of pending bookings for admin badge"""
    from .models import Booking
    count = Booking.objects.filter(status='Pending').count()
    return count
