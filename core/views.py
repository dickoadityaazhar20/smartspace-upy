from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Room, Booking, User, RoomComment, RoomReport
from .email_utils import send_welcome_email, send_booking_submitted_email


def home(request):
    """View untuk halaman utama - menampilkan daftar ruangan"""
    from .models import Testimonial
    
    rooms = Room.objects.filter(is_active=True).order_by('nomor_ruangan')
    testimonials = Testimonial.objects.filter(is_active=True).order_by('order', '-created_at')
    
    context = {
        'rooms': rooms,
        'testimonials': testimonials,
    }
    
    return render(request, 'home.html', context)


def rooms_list(request):
    """View untuk halaman daftar semua ruangan"""
    rooms = Room.objects.filter(is_active=True).order_by('nomor_ruangan')
    
    context = {
        'rooms': rooms,
    }
    
    return render(request, 'rooms_list.html', context)


def room_detail(request, pk):
    """View untuk detail ruangan dan form booking"""
    room = get_object_or_404(Room, pk=pk)
    
    # Form data to preserve on error
    form_data = {}
    
    if request.method == 'POST':
        nama_lengkap = request.POST.get('nama_lengkap', '')
        tanggal_mulai = request.POST.get('tanggal_mulai', '')
        tanggal_selesai = request.POST.get('tanggal_selesai', '')
        jumlah_tamu = request.POST.get('jumlah_tamu', '1')
        dokumen = request.FILES.get('dokumen_pendukung', None)
        
        # Preserve form data in case of error
        form_data = {
            'nama_lengkap': nama_lengkap,
            'tanggal_mulai': tanggal_mulai,
            'tanggal_selesai': tanggal_selesai,
            'jumlah_tamu': jumlah_tamu,
        }
        
        # Validasi sederhana
        errors = []
        
        if not nama_lengkap:
            errors.append('Nama lengkap wajib diisi')
        
        # Validasi jumlah tamu
        try:
            jumlah_tamu_int = int(jumlah_tamu)
            if jumlah_tamu_int < 1:
                errors.append('Jumlah tamu minimal 1 orang')
            elif jumlah_tamu_int > room.kapasitas:
                errors.append(f'Jumlah tamu melebihi kapasitas ruangan ({room.kapasitas} orang)')
        except (ValueError, TypeError):
            jumlah_tamu_int = 1
        
        # Validasi dokumen (WAJIB)
        if not dokumen:
            errors.append('Dokumen pendukung wajib diupload')
        else:
            allowed_extensions = ['.pdf', '.doc', '.docx']
            import os
            ext = os.path.splitext(dokumen.name)[1].lower()
            if ext not in allowed_extensions:
                errors.append('Format dokumen harus PDF, DOC, atau DOCX')
            elif dokumen.size > 5 * 1024 * 1024:  # 5MB max
                errors.append('Ukuran dokumen maksimal 5MB')
        
        dt_mulai = None
        dt_selesai = None
        
        if not tanggal_mulai or not tanggal_selesai:
            errors.append('Tanggal mulai dan selesai wajib diisi')
        else:
            # Parse datetime
            from datetime import datetime, timedelta
            try:
                dt_mulai = datetime.fromisoformat(tanggal_mulai)
                dt_selesai = datetime.fromisoformat(tanggal_selesai)
                
                # Make timezone aware if naive
                if timezone.is_naive(dt_mulai):
                    dt_mulai = timezone.make_aware(dt_mulai)
                if timezone.is_naive(dt_selesai):
                    dt_selesai = timezone.make_aware(dt_selesai)
                
                if dt_selesai <= dt_mulai:
                    errors.append('Tanggal selesai harus lebih besar dari tanggal mulai')
                
                # Allow 5 minutes buffer for form submission
                now_with_buffer = timezone.now() - timedelta(minutes=5)
                if dt_mulai < now_with_buffer:
                    errors.append('Tanggal mulai tidak boleh di masa lalu')
                    
            except ValueError:
                errors.append('Format tanggal tidak valid')
        

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Check for booking conflicts BEFORE creating
            conflict = Booking.check_conflict(room, dt_mulai, dt_selesai)
            if conflict:
                from django.utils import timezone as tz
                conflict_start = tz.localtime(conflict.tanggal_mulai).strftime('%H:%M')
                conflict_end = tz.localtime(conflict.tanggal_selesai).strftime('%H:%M')
                conflict_date = tz.localtime(conflict.tanggal_mulai).strftime('%d %b %Y')
                messages.error(
                    request, 
                    f'Maaf, jam {conflict_start}-{conflict_end} pada tanggal {conflict_date} '
                    f'sudah dibooking. Silakan pilih jam lain yang tersedia.'
                )
            else:
                # Buat booking baru
                # Cek apakah user login, jika tidak gunakan user pertama (untuk demo)
                if request.user.is_authenticated:
                    user = request.user
                else:
                    # Untuk demo, buat atau ambil user guest
                    user, created = User.objects.get_or_create(
                        username='guest',
                        defaults={
                            'first_name': nama_lengkap,
                            'email': 'guest@example.com',
                            'role': 'Mahasiswa'
                        }
                    )
                    if not created:
                        user.first_name = nama_lengkap
                        user.save()
                
                # Simpan booking
                booking = Booking.objects.create(
                    user=user,
                    room=room,
                    tanggal_mulai=dt_mulai,
                    tanggal_selesai=dt_selesai,
                    jumlah_tamu=jumlah_tamu_int,
                    dokumen_pendukung=dokumen,
                    status='Pending'
                )
                
                messages.success(
                    request, 
                    f'Peminjaman untuk "{room.nomor_ruangan}" berhasil diajukan! '
                    f'Status: Pending. Silakan tunggu konfirmasi dari admin.'
                )
                return redirect('home')
    
    context = {
        'room': room,
        'form_data': form_data,  # Pass form data back to template
    }
    
    return render(request, 'room_detail.html', context)


def report_room(request, pk):
    """View untuk melaporkan masalah ruangan"""
    room = get_object_or_404(Room, pk=pk)
    
    form_data = {}
    
    if request.method == 'POST':
        keterangan = request.POST.get('keterangan', '').strip()
        
        if not keterangan:
            messages.error(request, 'Keterangan wajib diisi!')
            form_data['keterangan'] = keterangan
        else:
            # Create room report
            user = request.user if request.user.is_authenticated else None
            RoomReport.objects.create(
                room=room,
                user=user,
                keterangan=keterangan
            )
            
            messages.success(
                request,
                f'Laporan untuk ruangan "{room.nomor_ruangan}" berhasil dikirim! '
                f'Terima kasih atas kontribusi Anda.'
            )
            return redirect('room_detail', pk=room.pk)
    
    context = {
        'room': room,
        'form_data': form_data,
    }
    
    return render(request, 'report_room.html', context)


def user_dashboard(request):
    """View untuk dashboard pengguna - menampilkan daftar peminjaman"""
    # Debug: Print to terminal to confirm this code is running
    print("=" * 50)
    print("DASHBOARD VIEW CALLED")
    print(f"User authenticated: {request.user.is_authenticated}")
    print(f"User: {request.user}")
    print(f"Database engine: {Booking.objects.db}")
    print("=" * 50)
    
    # Redirect to home with login required if not authenticated
    if not request.user.is_authenticated:
        print(">>> REDIRECTING: User not authenticated!")
        return redirect('/?login=required')
    
    # Get bookings for authenticated user only
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    
    # Pre-compute formatted values to avoid template tag line-break issues
    # Use Django's localtime to convert to local timezone
    from django.utils import timezone as tz
    bookings_list = []
    for booking in bookings:
        local_start = tz.localtime(booking.tanggal_mulai)
        local_end = tz.localtime(booking.tanggal_selesai)
        # Separate start date/time
        booking.formatted_start_date = local_start.strftime('%d %b %Y')
        booking.formatted_start_time = local_start.strftime('%H:%M')
        # Separate end date/time
        booking.formatted_end_date = local_end.strftime('%d %b %Y')
        booking.formatted_end_time = local_end.strftime('%H:%M')
        # Room icon based on type
        if booking.room.tipe_ruangan == 'Kelas':
            booking.room_icon = '🏫'
        elif booking.room.tipe_ruangan == 'Lab':
            booking.room_icon = '🔬'
        else:
            booking.room_icon = '🎭'
        bookings_list.append(booking)
    
    # Hitung statistik berdasarkan status (sesuai value di models.py)
    total_bookings = bookings.count()
    jumlah_pending = bookings.filter(status='Pending').count()
    jumlah_approved = bookings.filter(status='Approved').count()
    jumlah_rejected = bookings.filter(status='Rejected').count()
    jumlah_on_process = bookings.filter(status='On Process').count()
    jumlah_cancelled = bookings.filter(status='Cancelled').count()
    
    context = {
        'bookings': bookings_list,
        'total_bookings': total_bookings,
        'jumlah_pending': jumlah_pending,
        'jumlah_approved': jumlah_approved,
        'jumlah_rejected': jumlah_rejected,
        'jumlah_on_process': jumlah_on_process,
        'jumlah_cancelled': jumlah_cancelled,
    }
    
    return render(request, 'dashboard.html', context)


# ============================================
# AUTH API VIEWS
# ============================================
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.hashers import make_password
import json


@csrf_exempt
def api_register(request):
    """API endpoint untuk registrasi user baru"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['nama_lengkap', 'npm_nip', 'fakultas', 'program_studi', 'status', 'angkatan', 'email', 'nomor_hp', 'password']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'success': False, 'message': f'{field} wajib diisi'}, status=400)
        
        # Validate status value
        valid_roles = ['Mahasiswa', 'Dosen', 'Staff']
        role = data['status']
        if role not in valid_roles:
            return JsonResponse({'success': False, 'message': 'Status tidak valid'}, status=400)
        
        # Check if NPM/NIP already exists
        if User.objects.filter(npm_nip=data['npm_nip']).exists():
            return JsonResponse({'success': False, 'message': 'NPM/NIP sudah terdaftar'}, status=400)
        
        # Check if email already exists
        if User.objects.filter(email=data['email']).exists():
            return JsonResponse({'success': False, 'message': 'Email sudah terdaftar'}, status=400)
        
        # Create user with role from status field
        user = User.objects.create(
            username=data['npm_nip'],  # Use NPM/NIP as username
            email=data['email'],
            first_name=data['nama_lengkap'].split()[0] if data['nama_lengkap'] else '',
            last_name=' '.join(data['nama_lengkap'].split()[1:]) if len(data['nama_lengkap'].split()) > 1 else '',
            npm_nip=data['npm_nip'],
            fakultas=data['fakultas'],
            program_studi=data['program_studi'],
            angkatan=data['angkatan'],
            nomor_hp=data['nomor_hp'],
            password=make_password(data['password']),
            role=role  # Use status as role
        )
        
        # Auto login after register
        login(request, user)
        
        # Send welcome email (async, don't block response)
        try:
            send_welcome_email(user)
        except Exception as e:
            print(f"Failed to send welcome email: {e}")
        
        return JsonResponse({
            'success': True,
            'message': 'Registrasi berhasil!',
            'user': {
                'id': user.id,
                'nama': user.get_full_name() or user.username,
                'npm_nip': user.npm_nip,
                'email': user.email,
                'fakultas': user.fakultas,
                'program_studi': user.program_studi,
                'angkatan': user.angkatan,
                'role': user.role
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@csrf_exempt
def api_login(request):
    """API endpoint untuk login dengan NPM/NIP"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        npm_nip = data.get('npm_nip')
        password = data.get('password')
        
        if not npm_nip or not password:
            return JsonResponse({'success': False, 'message': 'NPM/NIP dan Password wajib diisi'}, status=400)
        
        # Find user by NPM/NIP
        try:
            user = User.objects.get(npm_nip=npm_nip)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'NPM/NIP tidak ditemukan'}, status=401)
        
        # Check password
        if not user.check_password(password):
            return JsonResponse({'success': False, 'message': 'Password salah'}, status=401)
        
        # Login user
        login(request, user)
        
        return JsonResponse({
            'success': True,
            'message': f'Login berhasil! Selamat datang, {user.get_full_name() or user.username}',
            'user': {
                'id': user.id,
                'nama': user.get_full_name() or user.username,
                'npm_nip': user.npm_nip,
                'email': user.email,
                'fakultas': user.fakultas,
                'program_studi': user.program_studi,
                'angkatan': user.angkatan,
                'role': user.role
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@csrf_exempt
def api_logout(request):
    """API endpoint untuk logout"""
    logout(request)
    return JsonResponse({'success': True, 'message': 'Logout berhasil'})


def api_check_auth(request):
    """API endpoint untuk cek status login"""
    if request.user.is_authenticated:
        from .models import Message
        unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()
        wishlist_count = request.user.wishlists.count()
        
        return JsonResponse({
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'nama': request.user.get_full_name() or request.user.username,
                'npm_nip': request.user.npm_nip,
                'email': request.user.email,
                'fakultas': request.user.fakultas,
                'program_studi': request.user.program_studi,
                'angkatan': request.user.angkatan,
                'nomor_hp': request.user.nomor_hp,
                'role': request.user.role,
                'unread_messages': unread_count,
                'wishlist_count': wishlist_count
            }
        })
    return JsonResponse({'authenticated': False})


@csrf_exempt
def api_forgot_password(request):
    """API endpoint untuk request reset password"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        email_or_npm = data.get('email_or_npm', '').strip()
        
        if not email_or_npm:
            return JsonResponse({'success': False, 'message': 'Email atau NPM/NIP wajib diisi'}, status=400)
        
        # Find user by email or NPM
        from django.db.models import Q
        user = User.objects.filter(Q(email=email_or_npm) | Q(npm_nip=email_or_npm)).first()
        
        if not user:
            # For security, don't reveal if user exists
            return JsonResponse({
                'success': True,
                'message': 'Jika email/NPM terdaftar, link reset password akan dikirim.'
            })
        
        # Create reset token
        from .models import PasswordResetToken
        from .email_utils import send_password_reset_email
        
        token_obj = PasswordResetToken.create_token(user)
        
        # Determine base URL
        base_url = request.build_absolute_uri('/').rstrip('/')
        
        # Send email
        send_password_reset_email(user, token_obj.token, base_url)
        
        return JsonResponse({
            'success': True,
            'message': 'Jika email/NPM terdaftar, link reset password akan dikirim.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"Error in forgot password: {e}")
        return JsonResponse({'success': False, 'message': 'Terjadi kesalahan server'}, status=500)


@csrf_exempt
def api_reset_password(request):
    """API endpoint untuk reset password dengan token"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        token = data.get('token', '').strip()
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        if not token:
            return JsonResponse({'success': False, 'message': 'Token tidak valid'}, status=400)
        
        if not new_password or len(new_password) < 6:
            return JsonResponse({'success': False, 'message': 'Password minimal 6 karakter'}, status=400)
        
        if new_password != confirm_password:
            return JsonResponse({'success': False, 'message': 'Konfirmasi password tidak cocok'}, status=400)
        
        # Find and validate token
        from .models import PasswordResetToken
        
        try:
            token_obj = PasswordResetToken.objects.get(token=token)
        except PasswordResetToken.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Link reset password tidak valid'}, status=400)
        
        if not token_obj.is_valid:
            return JsonResponse({'success': False, 'message': 'Link sudah kadaluarsa atau sudah digunakan'}, status=400)
        
        # Update password
        user = token_obj.user
        user.set_password(new_password)
        user.save()
        
        # Mark token as used
        token_obj.is_used = True
        token_obj.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Password berhasil direset! Silakan login dengan password baru.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"Error in reset password: {e}")
        return JsonResponse({'success': False, 'message': 'Terjadi kesalahan server'}, status=500)


def reset_password_page(request, token):
    """View untuk halaman reset password"""
    from .models import PasswordResetToken
    
    # Validate token
    try:
        token_obj = PasswordResetToken.objects.get(token=token)
        is_valid = token_obj.is_valid
    except PasswordResetToken.DoesNotExist:
        is_valid = False
    
    return render(request, 'reset_password.html', {
        'token': token,
        'is_valid': is_valid
    })


# ============================================
# WISHLIST API
# ============================================
from .models import Wishlist, Message

@csrf_exempt
def api_wishlist_toggle(request):
    """Toggle wishlist (add/remove) for a room"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Login required'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        room_id = data.get('room_id')
        
        if not room_id:
            return JsonResponse({'success': False, 'message': 'room_id required'}, status=400)
        
        room = Room.objects.get(pk=room_id)
        wishlist, created = Wishlist.objects.get_or_create(user=request.user, room=room)
        
        if not created:
            # Already exists, remove it
            wishlist.delete()
            return JsonResponse({
                'success': True,
                'action': 'removed',
                'message': f'{room.nomor_ruangan} dihapus dari wishlist',
                'wishlist_count': request.user.wishlists.count()
            })
        
        return JsonResponse({
            'success': True,
            'action': 'added',
            'message': f'{room.nomor_ruangan} ditambahkan ke wishlist',
            'wishlist_count': request.user.wishlists.count()
        })
        
    except Room.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Room not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


def api_wishlist_list(request):
    """Get user's wishlist"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Login required'}, status=401)
    
    wishlists = Wishlist.objects.filter(user=request.user).select_related('room')
    
    items = []
    for w in wishlists:
        items.append({
            'id': w.id,
            'room_id': w.room.id,
            'room_name': w.room.nomor_ruangan,
            'room_type': w.room.get_tipe_ruangan_display(),
            'capacity': w.room.kapasitas,
            'added_at': w.created_at.isoformat()
        })
    
    return JsonResponse({
        'success': True,
        'count': len(items),
        'items': items
    })


def api_wishlist_check(request, room_id):
    """Check if room is in user's wishlist"""
    if not request.user.is_authenticated:
        return JsonResponse({'in_wishlist': False})
    
    in_wishlist = Wishlist.objects.filter(user=request.user, room_id=room_id).exists()
    return JsonResponse({'in_wishlist': in_wishlist})


# ============================================
# PROFILE API
# ============================================
@csrf_exempt
def api_profile_update(request):
    """Update user profile"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Login required'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        user = request.user
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            # Check if email is used by another user
            if User.objects.filter(email=data['email']).exclude(pk=user.pk).exists():
                return JsonResponse({'success': False, 'message': 'Email sudah digunakan'}, status=400)
            user.email = data['email']
        if 'program_studi' in data:
            user.program_studi = data['program_studi']
        if 'fakultas' in data:
            user.fakultas = data['fakultas']
        if 'angkatan' in data:
            user.angkatan = data['angkatan']
        if 'nomor_hp' in data:
            user.nomor_hp = data['nomor_hp']
        
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Profil berhasil diperbarui',
            'user': {
                'id': user.id,
                'nama': user.get_full_name() or user.username,
                'npm_nip': user.npm_nip,
                'email': user.email,
                'fakultas': user.fakultas,
                'program_studi': user.program_studi,
                'angkatan': user.angkatan,
                'nomor_hp': user.nomor_hp,
                'role': user.role
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


def api_profile_get(request):
    """Get user profile data"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Login required'}, status=401)
    
    user = request.user
    return JsonResponse({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'npm_nip': user.npm_nip,
            'fakultas': user.fakultas,
            'program_studi': user.program_studi,
            'angkatan': user.angkatan,
            'nomor_hp': user.nomor_hp,
            'role': user.role,
            'date_joined': user.date_joined.isoformat()
        }
    })


# ============================================
# MESSAGES API
# ============================================
def api_messages_list(request):
    """Get user's messages"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Login required'}, status=401)
    
    messages = Message.objects.filter(receiver=request.user).select_related('sender')
    
    items = []
    for msg in messages:
        items.append({
            'id': msg.id,
            'sender_name': msg.sender.get_full_name() or msg.sender.username,
            'subject': msg.subject,
            'content': msg.content,
            'is_read': msg.is_read,
            'created_at': msg.created_at.isoformat()
        })
    
    return JsonResponse({
        'success': True,
        'count': len(items),
        'unread_count': Message.objects.filter(receiver=request.user, is_read=False).count(),
        'messages': items
    })


@csrf_exempt
def api_message_read(request, message_id):
    """Mark message as read"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Login required'}, status=401)
    
    try:
        message = Message.objects.get(pk=message_id, receiver=request.user)
        message.is_read = True
        message.save()
        
        return JsonResponse({
            'success': True,
            'unread_count': Message.objects.filter(receiver=request.user, is_read=False).count()
        })
    except Message.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Message not found'}, status=404)


def api_messages_count(request):
    """Get unread message count"""
    if not request.user.is_authenticated:
        return JsonResponse({'count': 0})
    
    count = Message.objects.filter(receiver=request.user, is_read=False).count()
    return JsonResponse({'count': count})


def api_messages_poll(request):
    """Poll for new messages - returns messages after a given ID"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Login required'}, status=401)
    
    user = request.user
    last_id = request.GET.get('last_id', 0)
    try:
        last_id = int(last_id)
    except:
        last_id = 0
    
    # Get ALL admin user IDs (superusers, Admin role, and staff)
    from django.db.models import Q
    all_admin_ids = list(User.objects.filter(
        Q(is_superuser=True) | Q(role='Admin') | Q(is_staff=True)
    ).values_list('id', flat=True))
    
    if not all_admin_ids:
        return JsonResponse({'success': True, 'messages': [], 'count': 0})
    
    # Get new messages between user and ANY admin
    new_messages = Message.objects.filter(
        Q(sender_id__in=all_admin_ids, receiver=user) |
        Q(sender=user, receiver_id__in=all_admin_ids)
    ).filter(id__gt=last_id).select_related('sender').order_by('created_at')
    
    # Mark incoming messages from any admin as read
    Message.objects.filter(
        sender_id__in=all_admin_ids,
        receiver=user,
        is_read=False
    ).update(is_read=True)
    
    messages_data = []
    for msg in new_messages:
        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'is_from_admin': msg.sender_id in all_admin_ids,
            'is_from_user': msg.sender == user,
            'time': msg.created_at.strftime('%d %b, %H:%M'),
            'attachment_url': msg.attachment.url if msg.attachment else None,
            'is_image': msg.is_image if hasattr(msg, 'is_image') else False
        })
    
    return JsonResponse({
        'success': True,
        'messages': messages_data,
        'count': len(messages_data)
    })


# ============================================
# PAGE VIEWS
# ============================================
def profile_page(request):
    """Profile page view"""
    if not request.user.is_authenticated:
        return redirect('/?login=required')
    
    user = request.user
    
    # Get booking statistics
    bookings = Booking.objects.filter(user=user)
    total_bookings = bookings.count()
    pending_bookings = bookings.filter(status='Pending').count()
    approved_bookings = bookings.filter(status='Approved').count()
    rejected_bookings = bookings.filter(status='Rejected').count()
    
    # Get wishlist and message counts
    wishlist_count = user.wishlists.count()
    unread_messages = Message.objects.filter(receiver=user, is_read=False).count()
    
    context = {
        'user': user,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'approved_bookings': approved_bookings,
        'rejected_bookings': rejected_bookings,
        'wishlist_count': wishlist_count,
        'unread_messages': unread_messages,
    }
    
    return render(request, 'profile.html', context)


def wishlist_page(request):
    """Wishlist page view"""
    if not request.user.is_authenticated:
        return redirect('/?login=required')
    
    wishlists = Wishlist.objects.filter(user=request.user).select_related('room')
    return render(request, 'wishlist.html', {'wishlists': wishlists})


def messages_page(request):
    """Messages page view - Chat with Admin"""
    if not request.user.is_authenticated:
        return redirect('/?login=required')
    
    # Get ALL admin users to query messages from any admin
    from django.db.models import Q
    all_admin_ids = list(User.objects.filter(
        Q(is_superuser=True) | Q(role='Admin') | Q(is_staff=True)
    ).values_list('id', flat=True))
    
    # Get the first admin for display purposes in header
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.filter(role='Admin').first()
    
    # Get all messages between this user and ANY admin (both directions)
    if all_admin_ids:
        conversation = Message.objects.filter(
            Q(sender=request.user, receiver_id__in=all_admin_ids) |
            Q(sender_id__in=all_admin_ids, receiver=request.user)
        ).select_related('sender', 'receiver').order_by('created_at')
        
        # Mark admin messages as read
        Message.objects.filter(
            sender_id__in=all_admin_ids, 
            receiver=request.user, 
            is_read=False
        ).update(is_read=True)
    else:
        conversation = Message.objects.none()
    
    unread_count = Message.objects.filter(
        receiver=request.user, 
        is_read=False
    ).count()
    
    # Get conversation message IDs as JSON for JavaScript
    conversation_ids_json = json.dumps([msg.id for msg in conversation])
    
    return render(request, 'messages.html', {
        'conversation': conversation,
        'conversation_ids_json': conversation_ids_json,
        'admin_user': admin_user,
        'unread_count': unread_count
    })


@csrf_exempt
def api_send_message(request):
    """API endpoint for user to send message to admin"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Login required'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        # Handle both JSON and multipart form data
        if request.content_type and 'multipart/form-data' in request.content_type:
            content = request.POST.get('content', '').strip()
            attachment = request.FILES.get('attachment')
        else:
            data = json.loads(request.body)
            content = data.get('content', '').strip()
            attachment = None
        
        if not content and not attachment:
            return JsonResponse({
                'success': False, 
                'message': 'Pesan atau lampiran wajib diisi'
            }, status=400)
        
        # Get admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.filter(role='Admin').first()
        
        if not admin_user:
            return JsonResponse({
                'success': False, 
                'message': 'Admin tidak ditemukan'
            }, status=404)
        
        # Validate attachment if present
        if attachment:
            # Check file size (max 10MB)
            if attachment.size > 10 * 1024 * 1024:
                return JsonResponse({
                    'success': False, 
                    'message': 'Ukuran file maksimal 10MB'
                }, status=400)
        
        # Create message
        message = Message.objects.create(
            sender=request.user,
            receiver=admin_user,
            content=content or 'Mengirim lampiran',
            message_type='user_to_admin',
            attachment=attachment,
            is_read=False
        )
        
        response_data = {
            'success': True,
            'message': 'Pesan terkirim',
            'data': {
                'id': message.id,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
                'attachment_url': message.attachment.url if message.attachment else None,
                'is_image': message.is_image,
                'attachment_filename': message.attachment_filename
            }
        }
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@csrf_exempt
def api_booking_cancel(request):
    """API endpoint to cancel a pending booking"""
    print("DEBUG: cancel request received")
    
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Login required'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        booking_id = data.get('booking_id')
        print(f"DEBUG: attempting to cancel booking_id={booking_id} for user={request.user}")
        
        if not booking_id:
            return JsonResponse({'success': False, 'message': 'booking_id required'}, status=400)
        
        # Get booking and verify ownership
        booking = Booking.objects.get(pk=booking_id, user=request.user)
        
        # Can only cancel pending bookings
        if booking.status != 'Pending':
            print(f"DEBUG: booking status is {booking.status}, cannot cancel")
            return JsonResponse({
                'success': False, 
                'message': f'Tidak dapat membatalkan peminjaman dengan status "{booking.status}"'
            }, status=400)
        
        # Set status to Cancelled instead of deleting
        room_name = booking.room.nomor_ruangan
        booking.status = 'Cancelled'
        booking.save()
        print(f"DEBUG: booking {booking_id} cancelled successfully")
        
        return JsonResponse({
            'success': True,
            'message': f'Peminjaman {room_name} berhasil dibatalkan'
        })
        
    except Booking.DoesNotExist:
        print("DEBUG: booking not found")
        return JsonResponse({'success': False, 'message': 'Peminjaman tidak ditemukan'}, status=404)
    except Exception as e:
        print(f"DEBUG: exception in cancel: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ============================================
# AI CHAT API
# ============================================
@csrf_exempt
def api_chat(request):
    """API endpoint for AI chatbot"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'success': False, 'message': 'Message required'}, status=400)
        
        # Get or create session ID (use user ID if authenticated, else session key)
        if request.user.is_authenticated:
            session_id = f"user_{request.user.id}"
        else:
            if not request.session.session_key:
                request.session.create()
            session_id = f"session_{request.session.session_key}"
        
        # Get AI service and send message
        from .ai_service import get_chat_service
        chat_service = get_chat_service()
        result = chat_service.chat(session_id, user_message)
        
        return JsonResponse({
            'success': result['success'],
            'response': result['response'],
            'error': result.get('error')
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': 'Terjadi kesalahan sistem',
            'response': 'Maaf, saya sedang mengalami gangguan. Silakan coba lagi nanti.'
        }, status=500)


# ============================================
# CALENDAR & BOOKING CONFLICT API
# ============================================
def api_calendar_bookings(request, room_id):
    """Get approved bookings for a room in a specific month for calendar display"""
    try:
        room = Room.objects.get(pk=room_id)
    except Room.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Room not found'}, status=404)
    
    # Get month/year from query params, default to current month
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    try:
        if year and month:
            year = int(year)
            month = int(month)
        else:
            from datetime import datetime
            now = datetime.now()
            year = now.year
            month = now.month
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Invalid year or month'}, status=400)
    
    # Get bookings for this room in this month
    bookings = Booking.get_approved_bookings_for_room(room, year, month)
    
    booking_data = []
    for booking in bookings:
        from django.utils import timezone as tz
        local_start = tz.localtime(booking.tanggal_mulai)
        local_end = tz.localtime(booking.tanggal_selesai)
        
        booking_data.append({
            'id': booking.id,
            'date': local_start.strftime('%Y-%m-%d'),
            'start_time': local_start.strftime('%H:%M'),
            'end_time': local_end.strftime('%H:%M'),
            'start_datetime': booking.tanggal_mulai.isoformat(),
            'end_datetime': booking.tanggal_selesai.isoformat(),
            'title': booking.keperluan[:50] if booking.keperluan else 'Tersedia',
            'user': booking.user.get_full_name() or booking.user.username,
            'status': booking.status
        })
    
    return JsonResponse({
        'success': True,
        'room': room.nomor_ruangan,
        'year': year,
        'month': month,
        'bookings': booking_data
    })


def api_booked_slots(request, room_id, date_str):
    """Get booked time slots for a room on a specific date.
    
    Returns array of {start_time, end_time} for each approved booking on that date.
    This is used by the time picker to disable already-booked slots.
    """
    try:
        room = Room.objects.get(pk=room_id)
    except Room.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Room not found'}, status=404)
    
    # Parse date string
    from datetime import datetime, time
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
    
    # Create datetime range for the whole day
    day_start = timezone.make_aware(datetime.combine(target_date, time.min))
    day_end = timezone.make_aware(datetime.combine(target_date, time.max))
    
    # Get approved bookings for this room on this date
    from django.db.models import Q
    bookings = Booking.objects.filter(
        room=room,
        status=Booking.Status.APPROVED
    ).filter(
        Q(tanggal_mulai__range=(day_start, day_end)) |
        Q(tanggal_selesai__range=(day_start, day_end)) |
        Q(tanggal_mulai__lt=day_start, tanggal_selesai__gt=day_end)
    ).order_by('tanggal_mulai')
    
    slots = []
    for booking in bookings:
        from django.utils import timezone as tz
        local_start = tz.localtime(booking.tanggal_mulai)
        local_end = tz.localtime(booking.tanggal_selesai)
        
        slots.append({
            'start_time': local_start.strftime('%H:%M'),
            'end_time': local_end.strftime('%H:%M'),
            'title': booking.keperluan[:30] if booking.keperluan else 'Booked'
        })
    
    # Calculate aggregated range for calendar display
    aggregated_range = None
    if slots:
        min_start = min(s['start_time'] for s in slots)
        max_end = max(s['end_time'] for s in slots)
        aggregated_range = f"{min_start}-{max_end}"
    
    return JsonResponse({
        'success': True,
        'date': date_str,
        'room': room.nomor_ruangan,
        'slots': slots,
        'aggregated_range': aggregated_range,
        'total_bookings': len(slots)
    })


@csrf_exempt
def api_check_booking_conflict(request):
    """Check if proposed booking time conflicts with existing approved bookings"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        room_id = data.get('room_id')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if not all([room_id, start_time, end_time]):
            return JsonResponse({
                'success': False, 
                'message': 'room_id, start_time, and end_time are required'
            }, status=400)
        
        # Get room
        try:
            room = Room.objects.get(pk=room_id)
        except Room.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Room not found'}, status=404)
        
        # Parse datetime
        from datetime import datetime
        try:
            dt_start = datetime.fromisoformat(start_time)
            dt_end = datetime.fromisoformat(end_time)
            
            # Make timezone aware if naive
            if timezone.is_naive(dt_start):
                dt_start = timezone.make_aware(dt_start)
            if timezone.is_naive(dt_end):
                dt_end = timezone.make_aware(dt_end)
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Invalid datetime format'}, status=400)
        
        # Check for conflicts
        conflict = Booking.check_conflict(room, dt_start, dt_end)
        
        if conflict:
            from django.utils import timezone as tz
            local_start = tz.localtime(conflict.tanggal_mulai)
            local_end = tz.localtime(conflict.tanggal_selesai)
            
            return JsonResponse({
                'success': True,
                'has_conflict': True,
                'conflict': {
                    'id': conflict.id,
                    'title': conflict.keperluan[:50] if conflict.keperluan else 'Booking',
                    'start_time': local_start.strftime('%H:%M'),
                    'end_time': local_end.strftime('%H:%M'),
                    'date': local_start.strftime('%d %b %Y'),
                    'user': conflict.user.get_full_name() or conflict.user.username
                },
                'message': f"Jam {local_start.strftime('%H:%M')}-{local_end.strftime('%H:%M')} sudah dibooking untuk '{conflict.keperluan[:30]}'. Pilih jam lain yang tersedia."
            })
        
        return JsonResponse({
            'success': True,
            'has_conflict': False,
            'message': 'Waktu tersedia untuk booking'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ============================================
# FEEDBACK API (Kritik & Saran)
# ============================================
from .models import Feedback

def feedback_page(request):
    """Halaman Kritik & Saran untuk user submit feedback"""
    return render(request, 'feedback.html')


@csrf_exempt
def api_feedback_submit(request):
    """API endpoint untuk submit feedback Kritik & Saran (Anonymous)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Get data - nama and email are optional (anonymous by default)
        category = data.get('category', 'saran')
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()
        
        # Only validate subject and message
        if not subject:
            return JsonResponse({'success': False, 'message': 'Subjek wajib diisi'}, status=400)
        if not message:
            return JsonResponse({'success': False, 'message': 'Pesan wajib diisi'}, status=400)
        
        # Validate category
        valid_categories = ['kritik', 'saran', 'lainnya']
        if category not in valid_categories:
            category = 'saran'
        
        # Create anonymous feedback
        feedback = Feedback.objects.create(
            user=request.user if request.user.is_authenticated else None,
            nama='Anonymous',
            email='anonymous@feedback.local',
            category=category,
            subject=subject,
            message=message
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Terima kasih! Feedback anonim Anda sudah kami terima.',
            'feedback_id': feedback.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ============================================
# ROOM COMMENTS & RATING API
# ============================================

@csrf_exempt
def api_submit_comment(request, room_id):
    """API endpoint untuk submit komentar dan rating ruangan"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Silakan login terlebih dahulu'}, status=401)
    
    try:
        data = json.loads(request.body)
        rating = int(data.get('rating', 0))
        comment = data.get('comment', '').strip()
        
        if rating < 1 or rating > 5:
            return JsonResponse({'success': False, 'message': 'Rating harus 1-5'}, status=400)
        
        if not comment:
            return JsonResponse({'success': False, 'message': 'Komentar wajib diisi'}, status=400)
        
        room = get_object_or_404(Room, pk=room_id)
        
        # Check if user already commented
        existing = RoomComment.objects.filter(user=request.user, room=room).first()
        if existing:
            # Update existing comment
            existing.rating = rating
            existing.comment = comment
            existing.save()
            return JsonResponse({'success': True, 'message': 'Komentar berhasil diupdate!'})
        
        # Create new comment
        RoomComment.objects.create(
            user=request.user,
            room=room,
            rating=rating,
            comment=comment
        )
        
        return JsonResponse({'success': True, 'message': 'Komentar berhasil ditambahkan!'})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


def api_room_comments(request, room_id):
    """API endpoint untuk get komentar ruangan"""
    try:
        room = get_object_or_404(Room, pk=room_id)
        comments = room.comments.filter(is_approved=True).select_related('user')
        
        comments_data = [{
            'id': c.id,
            'user_name': c.user.get_full_name() or c.user.username,
            'user_initial': (c.user.first_name[:1] if c.user.first_name else c.user.username[:1]).upper(),
            'rating': c.rating,
            'comment': c.comment,
            'created_at': c.created_at.strftime('%d %b %Y, %H:%M')
        } for c in comments]
        
        return JsonResponse({
            'success': True,
            'comments': comments_data,
            'average_rating': float(room.average_rating),
            'total_reviews': room.total_reviews
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
