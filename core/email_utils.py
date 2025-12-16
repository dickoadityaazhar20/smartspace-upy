"""
Email Utility Module for SmartSpace UPY
Uses Brevo (Sendinblue) API for sending emails
"""
from django.conf import settings
from django.utils import timezone
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException


# Configure Brevo API
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = getattr(settings, 'BREVO_API_KEY', '')


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """
    Send an email using Brevo (Sendinblue) API
    Returns True if successful, False otherwise
    Uses HTTP API - works on Railway and other platforms that block SMTP
    """
    try:
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
        
        sender = {"name": settings.EMAIL_FROM_NAME, "email": "dickoadityaazhar20@gmail.com"}
        to = [{"email": to_email}]
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=to,
            sender=sender,
            subject=subject,
            html_content=html_content
        )
        
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(f"Email sent successfully to {to_email}: {api_response}")
        return True
    except ApiException as e:
        print(f"Brevo API error sending email to {to_email}: {e}")
        return False
    except Exception as e:
        print(f"Error sending email to {to_email}: {str(e)}")
        return False


def send_welcome_email(user) -> bool:
    """Send welcome email after registration"""
    subject = "🎉 Selamat Datang di SmartSpace UPY!"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #3B82F6, #1D4ED8); padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .header h1 {{ color: white; margin: 0; font-size: 24px; }}
            .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 12px 12px; }}
            .info-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3B82F6; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            .btn {{ display: inline-block; padding: 12px 24px; background: #3B82F6; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏢 SmartSpace UPY</h1>
            </div>
            <div class="content">
                <h2>Halo, {user.get_full_name() or user.username}! 👋</h2>
                <p>Selamat datang di <strong>SmartSpace UPY</strong> - Sistem Peminjaman Ruangan Universitas PGRI Yogyakarta.</p>
                
                <div class="info-box">
                    <h3 style="margin-top: 0;">📋 Data Akun Anda:</h3>
                    <p><strong>NPM/NIP:</strong> {user.npm_nip}</p>
                    <p><strong>Email:</strong> {user.email}</p>
                    <p><strong>Fakultas:</strong> {user.fakultas or '-'}</p>
                    <p><strong>Program Studi:</strong> {user.program_studi or '-'}</p>
                    <p><strong>Status:</strong> {user.role}</p>
                </div>
                
                <p>Anda sekarang dapat:</p>
                <ul>
                    <li>🔍 Melihat daftar ruangan yang tersedia</li>
                    <li>📅 Melakukan booking ruangan</li>
                    <li>📊 Memantau status peminjaman</li>
                </ul>
                
                <p style="text-align: center; margin-top: 30px;">
                    <a href="http://127.0.0.1:8000/" class="btn">Mulai Booking Sekarang</a>
                </p>
            </div>
            <div class="footer">
                <p>© 2024 SmartSpace UPY - Universitas PGRI Yogyakarta</p>
                <p>Email ini dikirim secara otomatis, mohon tidak membalas email ini.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user.email, subject, html_content)


def send_booking_submitted_email(booking) -> bool:
    """Send email when booking is submitted"""
    user = booking.user
    subject = "📋 Booking Anda Sedang Diproses - SmartSpace UPY"
    
    tanggal_mulai = timezone.localtime(booking.tanggal_mulai)
    tanggal_selesai = timezone.localtime(booking.tanggal_selesai)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #F59E0B, #D97706); padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .header h1 {{ color: white; margin: 0; font-size: 24px; }}
            .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 12px 12px; }}
            .info-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #F59E0B; }}
            .status {{ display: inline-block; padding: 6px 12px; background: #FEF3C7; color: #92400E; border-radius: 20px; font-weight: bold; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📋 Booking Sedang Diproses</h1>
            </div>
            <div class="content">
                <h2>Halo, {user.get_full_name() or user.username}!</h2>
                <p>Booking Anda telah kami terima dan sedang dalam proses review oleh admin.</p>
                
                <div class="info-box">
                    <h3 style="margin-top: 0;">📅 Detail Booking:</h3>
                    <p><strong>Ruangan:</strong> {booking.room.nomor_ruangan}</p>
                    <p><strong>Tanggal:</strong> {tanggal_mulai.strftime('%d %B %Y')}</p>
                    <p><strong>Waktu:</strong> {tanggal_mulai.strftime('%H:%M')} - {tanggal_selesai.strftime('%H:%M')} WIB</p>
                    <p><strong>Keperluan:</strong> {booking.keperluan}</p>
                    <p><strong>Jumlah Peserta:</strong> {booking.jumlah_tamu or '-'} orang</p>
                    <p><strong>Status:</strong> <span class="status">⏳ Pending</span></p>
                </div>
                
                <p>Kami akan mengirimkan email notifikasi saat status booking Anda diperbarui.</p>
            </div>
            <div class="footer">
                <p>© 2024 SmartSpace UPY - Universitas PGRI Yogyakarta</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user.email, subject, html_content)


def send_booking_approved_email(booking) -> bool:
    """Send email when booking is approved"""
    user = booking.user
    subject = "✅ Booking Anda Disetujui! - SmartSpace UPY"
    
    tanggal_mulai = timezone.localtime(booking.tanggal_mulai)
    tanggal_selesai = timezone.localtime(booking.tanggal_selesai)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #10B981, #059669); padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .header h1 {{ color: white; margin: 0; font-size: 24px; }}
            .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 12px 12px; }}
            .info-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10B981; }}
            .status {{ display: inline-block; padding: 6px 12px; background: #D1FAE5; color: #065F46; border-radius: 20px; font-weight: bold; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            .important {{ background: #ECFDF5; padding: 15px; border-radius: 8px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✅ Booking Disetujui!</h1>
            </div>
            <div class="content">
                <h2>Selamat, {user.get_full_name() or user.username}! 🎉</h2>
                <p>Booking ruangan Anda telah <strong>DISETUJUI</strong> oleh admin.</p>
                
                <div class="info-box">
                    <h3 style="margin-top: 0;">📅 Detail Booking:</h3>
                    <p><strong>Ruangan:</strong> {booking.room.nomor_ruangan}</p>
                    <p><strong>Tanggal:</strong> {tanggal_mulai.strftime('%d %B %Y')}</p>
                    <p><strong>Waktu:</strong> {tanggal_mulai.strftime('%H:%M')} - {tanggal_selesai.strftime('%H:%M')} WIB</p>
                    <p><strong>Keperluan:</strong> {booking.keperluan}</p>
                    <p><strong>Status:</strong> <span class="status">✅ Approved</span></p>
                </div>
                
                <div class="important">
                    <strong>📌 Penting:</strong>
                    <ul style="margin: 10px 0;">
                        <li>Harap datang tepat waktu sesuai jadwal</li>
                        <li>Jaga kebersihan dan kerapian ruangan</li>
                        <li>Kembalikan peralatan ke posisi semula setelah selesai</li>
                    </ul>
                </div>
            </div>
            <div class="footer">
                <p>© 2024 SmartSpace UPY - Universitas PGRI Yogyakarta</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user.email, subject, html_content)


def send_booking_rejected_email(booking) -> bool:
    """Send email when booking is rejected"""
    user = booking.user
    subject = "❌ Booking Anda Ditolak - SmartSpace UPY"
    
    tanggal_mulai = timezone.localtime(booking.tanggal_mulai)
    tanggal_selesai = timezone.localtime(booking.tanggal_selesai)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #EF4444, #DC2626); padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .header h1 {{ color: white; margin: 0; font-size: 24px; }}
            .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 12px 12px; }}
            .info-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #EF4444; }}
            .status {{ display: inline-block; padding: 6px 12px; background: #FEE2E2; color: #991B1B; border-radius: 20px; font-weight: bold; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            .btn {{ display: inline-block; padding: 12px 24px; background: #3B82F6; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>❌ Booking Ditolak</h1>
            </div>
            <div class="content">
                <h2>Halo, {user.get_full_name() or user.username}</h2>
                <p>Mohon maaf, booking ruangan Anda <strong>tidak dapat disetujui</strong>.</p>
                
                <div class="info-box">
                    <h3 style="margin-top: 0;">📅 Detail Booking:</h3>
                    <p><strong>Ruangan:</strong> {booking.room.nomor_ruangan}</p>
                    <p><strong>Tanggal:</strong> {tanggal_mulai.strftime('%d %B %Y')}</p>
                    <p><strong>Waktu:</strong> {tanggal_mulai.strftime('%H:%M')} - {tanggal_selesai.strftime('%H:%M')} WIB</p>
                    <p><strong>Keperluan:</strong> {booking.keperluan}</p>
                    <p><strong>Status:</strong> <span class="status">❌ Rejected</span></p>
                </div>
                
                <p>Kemungkinan alasan penolakan:</p>
                <ul>
                    <li>Ruangan sudah dipesan untuk waktu tersebut</li>
                    <li>Dokumen pendukung tidak lengkap</li>
                    <li>Keperluan tidak sesuai kebijakan</li>
                </ul>
                
                <p>Silakan coba booking ruangan lain atau waktu yang berbeda.</p>
                
                <p style="text-align: center; margin-top: 30px;">
                    <a href="http://127.0.0.1:8000/" class="btn">Coba Booking Lagi</a>
                </p>
            </div>
            <div class="footer">
                <p>© 2024 SmartSpace UPY - Universitas PGRI Yogyakarta</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user.email, subject, html_content)


def send_booking_reminder_email(booking) -> bool:
    """Send H-1 reminder email for upcoming booking"""
    user = booking.user
    subject = "📅 Pengingat: Booking Anda Besok! - SmartSpace UPY"
    
    tanggal_mulai = timezone.localtime(booking.tanggal_mulai)
    tanggal_selesai = timezone.localtime(booking.tanggal_selesai)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #8B5CF6, #7C3AED); padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .header h1 {{ color: white; margin: 0; font-size: 24px; }}
            .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 12px 12px; }}
            .info-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #8B5CF6; }}
            .reminder {{ background: #EDE9FE; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⏰ Pengingat Booking</h1>
            </div>
            <div class="content">
                <h2>Halo, {user.get_full_name() or user.username}!</h2>
                
                <div class="reminder">
                    <h3 style="margin: 0; color: #7C3AED;">📅 BESOK!</h3>
                    <p style="font-size: 18px; margin: 10px 0 0 0;">Anda memiliki booking ruangan</p>
                </div>
                
                <div class="info-box">
                    <h3 style="margin-top: 0;">📋 Detail Booking:</h3>
                    <p><strong>Ruangan:</strong> {booking.room.nomor_ruangan}</p>
                    <p><strong>Tanggal:</strong> {tanggal_mulai.strftime('%d %B %Y')}</p>
                    <p><strong>Waktu:</strong> {tanggal_mulai.strftime('%H:%M')} - {tanggal_selesai.strftime('%H:%M')} WIB</p>
                    <p><strong>Keperluan:</strong> {booking.keperluan}</p>
                </div>
                
                <p><strong>📌 Hal yang perlu dipersiapkan:</strong></p>
                <ul>
                    <li>Datang 10-15 menit sebelum waktu mulai</li>
                    <li>Bawa kartu identitas (KTM/ID Pegawai)</li>
                    <li>Pastikan peralatan yang dibutuhkan sudah siap</li>
                </ul>
            </div>
            <div class="footer">
                <p>© 2024 SmartSpace UPY - Universitas PGRI Yogyakarta</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user.email, subject, html_content)


def send_password_reset_email(user, token: str, base_url: str = "https://smartspaceupy.up.railway.app") -> bool:
    """Send password reset email with link"""
    subject = "🔐 Reset Password - SmartSpace UPY"
    reset_link = f"{base_url}/reset-password/{token}/"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #3B82F6, #1D4ED8); padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .header h1 {{ color: white; margin: 0; font-size: 24px; }}
            .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 12px 12px; }}
            .info-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3B82F6; text-align: center; }}
            .btn {{ display: inline-block; padding: 14px 28px; background: #3B82F6; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; }}
            .btn:hover {{ background: #2563EB; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            .warning {{ background: #FEF3C7; padding: 15px; border-radius: 8px; margin-top: 20px; color: #92400E; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Reset Password</h1>
            </div>
            <div class="content">
                <h2>Halo, {user.get_full_name() or user.username}!</h2>
                <p>Kami menerima permintaan untuk mereset password akun SmartSpace UPY Anda.</p>
                
                <div class="info-box">
                    <p style="margin-bottom: 20px;">Klik tombol di bawah untuk membuat password baru:</p>
                    <a href="{reset_link}" class="btn">Reset Password Sekarang</a>
                </div>
                
                <div class="warning">
                    <strong>⚠️ Penting:</strong>
                    <ul style="margin: 10px 0;">
                        <li>Link ini hanya berlaku selama <strong>1 jam</strong></li>
                        <li>Jika Anda tidak meminta reset password, abaikan email ini</li>
                        <li>Jangan bagikan link ini kepada siapapun</li>
                    </ul>
                </div>
                
                <p style="margin-top: 20px; font-size: 12px; color: #666;">
                    Jika tombol tidak berfungsi, copy link berikut ke browser:<br>
                    <code style="background: #e5e7eb; padding: 2px 6px; border-radius: 4px;">{reset_link}</code>
                </p>
            </div>
            <div class="footer">
                <p>© 2024 SmartSpace UPY - Universitas PGRI Yogyakarta</p>
                <p>Email ini dikirim secara otomatis, mohon tidak membalas email ini.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user.email, subject, html_content)
