from django.db import models
from django.contrib.auth.models import AbstractUser
import os


# Get appropriate storage for documents (PDFs, DOCs)
def get_document_storage():
    """Return RawMediaCloudinaryStorage in production, None (default) in development"""
    if os.getenv('CLOUDINARY_CLOUD_NAME'):
        from cloudinary_storage.storage import RawMediaCloudinaryStorage
        return RawMediaCloudinaryStorage()
    return None


class User(AbstractUser):
    """Custom User model extending AbstractUser"""
    
    class Role(models.TextChoices):
        MAHASISWA = 'Mahasiswa', 'Mahasiswa'
        DOSEN = 'Dosen', 'Dosen'
        STAFF = 'Staff', 'Staff'
        ADMIN = 'Admin', 'Admin'
    
    class Fakultas(models.TextChoices):
        FST = 'FST', 'Fakultas Sains Dan Teknologi'
        FP = 'FP', 'Fakultas Pertanian'
        FBH = 'FBH', 'Fakultas Bisnis Dan Hukum'
        FKIP = 'FKIP', 'Fakultas Keguruan Dan Ilmu Pendidikan'
    
    npm_nip = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='NPM/NIP')
    fakultas = models.CharField(
        max_length=20,
        choices=Fakultas.choices,
        blank=True,
        null=True,
        verbose_name='Fakultas'
    )
    program_studi = models.CharField(max_length=100, blank=True, null=True, verbose_name='Program Studi')
    angkatan = models.CharField(max_length=20, blank=True, null=True, verbose_name='Angkatan')
    nomor_hp = models.CharField(max_length=20, blank=True, null=True, verbose_name='Nomor HP/WhatsApp')
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MAHASISWA,
        verbose_name='Role'
    )
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Room(models.Model):
    """Model untuk Ruangan"""
    
    class TipeRuangan(models.TextChoices):
        KELAS = 'Kelas', 'Kelas'
        LAB = 'Lab', 'Lab'
        AULA = 'Aula', 'Aula'
    
    class RoomStatus(models.TextChoices):
        AVAILABLE = 'available', 'Tersedia'
        MAINTENANCE = 'maintenance', 'Dalam Perbaikan'
        UNAVAILABLE = 'unavailable', 'Tidak Tersedia'
    
    nomor_ruangan = models.CharField(max_length=50, unique=True, verbose_name='Nama Ruangan')
    tipe_ruangan = models.CharField(
        max_length=20,
        choices=TipeRuangan.choices,
        default=TipeRuangan.KELAS,
        verbose_name='Tipe Ruangan'
    )
    kapasitas = models.PositiveIntegerField(default=0, verbose_name='Kapasitas')
    fasilitas = models.TextField(
        blank=True, 
        verbose_name='Fasilitas',
        help_text='Daftar fasilitas ruangan (satu fasilitas per baris, tekan Enter untuk menambah)'
    )
    foto_ruangan = models.ImageField(upload_to='ruangan/', blank=True, null=True, verbose_name='Upload Foto')
    foto_url = models.URLField(
        blank=True, 
        null=True, 
        verbose_name='URL Gambar',
        help_text='Alternatif: masukkan URL langsung ke gambar'
    )
    foto_drive_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name='Google Drive ID',
        help_text='Alternatif: masukkan ID file dari Google Drive (contoh: 1aBcDeFgHiJkLmNoPqRs)'
    )
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    
    # Room Status Fields
    status = models.CharField(
        max_length=20,
        choices=RoomStatus.choices,
        default=RoomStatus.AVAILABLE,
        verbose_name='Status Ruangan'
    )
    maintenance_note = models.TextField(
        blank=True,
        verbose_name='Catatan Perbaikan',
        help_text='Alasan atau detail perbaikan (opsional)'
    )
    maintenance_end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Estimasi Selesai',
        help_text='Perkiraan tanggal ruangan tersedia kembali (opsional)'
    )
    
    # CMS Fields
    deskripsi = models.TextField(
        blank=True, 
        verbose_name='Deskripsi Ruangan',
        help_text='Deskripsi lengkap tentang ruangan ini'
    )
    peraturan = models.TextField(
        blank=True, 
        verbose_name='Hal yang Diperbolehkan ✅',
        help_text='Hal-hal yang BOLEH dilakukan di ruangan ini (pisahkan dengan baris baru)'
    )
    larangan = models.TextField(
        blank=True, 
        verbose_name='Hal yang Dilarang ❌',
        help_text='Hal-hal yang TIDAK BOLEH dilakukan di ruangan ini (pisahkan dengan baris baru)'
    )
    
    # Rating fields (auto-calculated from comments)
    average_rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=0,
        verbose_name='Rating Rata-rata'
    )
    total_reviews = models.PositiveIntegerField(
        default=0,
        verbose_name='Jumlah Review'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Ruangan'
        verbose_name_plural = 'Ruangan'
        ordering = ['nomor_ruangan']
    
    def __str__(self):
        return f"{self.nomor_ruangan} - {self.get_tipe_ruangan_display()}"
    
    @property
    def get_foto_url(self):
        """Return foto URL dengan prioritas: upload > url > drive > None"""
        # Check uploaded file first (must have a name/path)
        if self.foto_ruangan and self.foto_ruangan.name:
            try:
                return self.foto_ruangan.url
            except Exception:
                pass  # Fall through to other options
        
        # Check URL field
        if self.foto_url:
            return self.foto_url
        
        # Check Google Drive ID
        if self.foto_drive_id:
            return f"https://drive.google.com/uc?export=view&id={self.foto_drive_id}"
        
        return None
    
    @property
    def fasilitas_list(self):
        """Return fasilitas as a list, splitting by newlines"""
        if self.fasilitas:
            return [f.strip() for f in self.fasilitas.split('\n') if f.strip()]
        return []
    
    @property
    def peraturan_list(self):
        """Return peraturan (allowed rules) as a list, splitting by newlines"""
        if self.peraturan:
            return [p.strip() for p in self.peraturan.split('\n') if p.strip()]
        return []
    
    @property
    def larangan_list(self):
        """Return larangan (prohibited rules) as a list, splitting by newlines"""
        if self.larangan:
            return [l.strip() for l in self.larangan.split('\n') if l.strip()]
        return []
    
    @property
    def is_available(self):
        """Check if room is available for booking"""
        return self.status == 'available'
    
    @property
    def is_maintenance(self):
        """Check if room is under maintenance"""
        return self.status == 'maintenance'
    
    @property
    def status_display_info(self):
        """Returns dict with label, color, icon for templates"""
        status_map = {
            'available': {'label': 'Tersedia', 'color': 'green', 'icon': '✓'},
            'maintenance': {'label': 'Dalam Perbaikan', 'color': 'yellow', 'icon': '🔧'},
            'unavailable': {'label': 'Tidak Tersedia', 'color': 'red', 'icon': '✕'},
        }
        return status_map.get(self.status, status_map['unavailable'])
    
    def update_average_rating(self):
        """Update average rating based on approved comments"""
        from django.db.models import Avg, Count
        result = self.comments.filter(is_approved=True).aggregate(
            avg_rating=Avg('rating'),
            count=Count('id')
        )
        self.average_rating = round(result['avg_rating'] or 0, 1)
        self.total_reviews = result['count'] or 0
        self.save(update_fields=['average_rating', 'total_reviews'])


class Booking(models.Model):
    """Model untuk Peminjaman Ruangan"""
    
    class Status(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        APPROVED = 'Approved', 'Approved'
        REJECTED = 'Rejected', 'Rejected'
        ON_PROCESS = 'On Process', 'On Process'
        CANCELLED = 'Cancelled', 'Dibatalkan'
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='User'
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Ruangan'
    )
    tanggal_mulai = models.DateTimeField(verbose_name='Tanggal Mulai')
    tanggal_selesai = models.DateTimeField(verbose_name='Tanggal Selesai')
    jumlah_tamu = models.PositiveIntegerField(
        default=1,
        verbose_name='Jumlah Tamu',
        help_text='Jumlah peserta/tamu yang akan hadir'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Status'
    )
    keperluan = models.TextField(blank=True, verbose_name='Keperluan')
    dokumen_pendukung = models.FileField(
        upload_to='dokumen_booking/',
        storage=get_document_storage(),
        blank=True,
        null=True,
        verbose_name='Dokumen Pendukung',
        help_text='Upload dokumen pendukung (hanya PDF)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Peminjaman'
        verbose_name_plural = 'Peminjaman'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Booking {self.room.nomor_ruangan} by {self.user.username} - {self.get_status_display()}"
    
    @classmethod
    def check_conflict(cls, room, start_time, end_time, exclude_booking_id=None):
        """
        Check if proposed booking conflicts with existing approved OR pending bookings.
        Returns conflicting booking if found, None otherwise.
        """
        from django.db.models import Q
        
        # Check for conflicts with APPROVED or PENDING bookings
        conflicts = cls.objects.filter(
            room=room,
            tanggal_mulai__lt=end_time,
            tanggal_selesai__gt=start_time
        ).filter(
            Q(status=cls.Status.APPROVED) | Q(status=cls.Status.PENDING)
        )
        if exclude_booking_id:
            conflicts = conflicts.exclude(pk=exclude_booking_id)
        return conflicts.first()
    
    @classmethod
    def get_approved_bookings_for_room(cls, room, year, month):
        """
        Get all approved bookings for a room in a specific month.
        Returns QuerySet of bookings.
        """
        from django.db.models import Q
        from django.utils import timezone
        from datetime import datetime
        import calendar
        
        # Get first and last day of month with proper timezone
        first_day_naive = datetime(year, month, 1, 0, 0, 0)
        last_day_naive = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)
        
        # Make timezone aware using the configured timezone (Asia/Jakarta)
        first_day = timezone.make_aware(first_day_naive)
        last_day = timezone.make_aware(last_day_naive)
        
        return cls.objects.filter(
            room=room,
            status=cls.Status.APPROVED,
        ).filter(
            Q(tanggal_mulai__range=(first_day, last_day)) |
            Q(tanggal_selesai__range=(first_day, last_day)) |
            Q(tanggal_mulai__lt=first_day, tanggal_selesai__gt=last_day)
        ).order_by('tanggal_mulai')


class Wishlist(models.Model):
    """Model untuk Wishlist/Favorit Ruangan"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wishlists',
        verbose_name='User'
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='wishlists',
        verbose_name='Ruangan'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Wishlist'
        verbose_name_plural = 'Wishlists'
        unique_together = ['user', 'room']  # Prevent duplicates
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.room.nomor_ruangan}"


class Message(models.Model):
    """Model untuk Pesan dua arah antara User dan Admin"""
    
    class MessageType(models.TextChoices):
        USER_TO_ADMIN = 'user_to_admin', 'User ke Admin'
        ADMIN_TO_USER = 'admin_to_user', 'Admin ke User'
    
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Pengirim'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name='Penerima'
    )
    subject = models.CharField(
        max_length=200, 
        blank=True,
        default='',
        verbose_name='Subjek'
    )
    content = models.TextField(verbose_name='Isi Pesan')
    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.ADMIN_TO_USER,
        verbose_name='Tipe Pesan'
    )
    attachment = models.FileField(
        upload_to='message_attachments/',
        blank=True,
        null=True,
        verbose_name='Lampiran',
        help_text='File lampiran (gambar, dokumen, dll)'
    )
    is_read = models.BooleanField(default=False, verbose_name='Sudah Dibaca')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Pesan'
        verbose_name_plural = 'Pesan'
        ordering = ['created_at']  # Oldest first for chat display
    
    def __str__(self):
        return f"Dari {self.sender.username} ke {self.receiver.username}: {self.content[:30]}"
    
    @property
    def is_image(self):
        """Check if attachment is an image"""
        if self.attachment:
            ext = self.attachment.name.lower().split('.')[-1]
            return ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']
        return False
    
    @property
    def attachment_filename(self):
        """Get just the filename from attachment"""
        if self.attachment:
            return self.attachment.name.split('/')[-1]
        return None


class PinnedConversation(models.Model):
    """Model untuk menyimpan percakapan yang di-pin oleh admin"""
    
    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pinned_conversations',
        verbose_name='Admin'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pinned_by',
        verbose_name='User'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Pinned Conversation'
        verbose_name_plural = 'Pinned Conversations'
        unique_together = ('admin', 'user')
    
    def __str__(self):
        return f"{self.admin.username} pinned {self.user.username}"


class Testimonial(models.Model):
    """Model untuk Testimoni yang tampil di Homepage"""
    
    nama = models.CharField(max_length=100, verbose_name='Nama')
    role = models.CharField(
        max_length=100, 
        verbose_name='Jabatan/Role',
        help_text='Contoh: Mahasiswa Teknik Informatika, Dosen FKIP, Staff Akademik'
    )
    foto = models.ImageField(
        upload_to='testimonials/', 
        blank=True, 
        null=True, 
        verbose_name='Foto',
        help_text='Foto profil (opsional, ukuran rekomendasi: 100x100px)'
    )
    content = models.TextField(
        verbose_name='Isi Testimoni',
        help_text='Testimoni tentang pengalaman menggunakan SmartSpace UPY'
    )
    rating = models.PositiveIntegerField(
        default=5,
        verbose_name='Rating',
        help_text='Rating 1-5 bintang'
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name='Aktif',
        help_text='Centang untuk menampilkan di homepage'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Urutan',
        help_text='Urutan tampil (angka kecil tampil duluan)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Testimoni'
        verbose_name_plural = 'Testimoni'
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return f"{self.nama} - {self.role}"
    
    def save(self, *args, **kwargs):
        # Ensure rating is between 1 and 5
        if self.rating < 1:
            self.rating = 1
        elif self.rating > 5:
            self.rating = 5
        super().save(*args, **kwargs)


class Feedback(models.Model):
    """Model untuk Kritik dan Saran dari User"""
    
    class Category(models.TextChoices):
        KRITIK = 'kritik', 'Kritik'
        SARAN = 'saran', 'Saran'
        LAINNYA = 'lainnya', 'Lainnya'
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='feedbacks',
        verbose_name='User'
    )
    nama = models.CharField(max_length=100, verbose_name='Nama')
    email = models.EmailField(verbose_name='Email')
    category = models.CharField(
        max_length=20, 
        choices=Category.choices,
        default=Category.SARAN,
        verbose_name='Kategori'
    )
    subject = models.CharField(max_length=200, verbose_name='Subjek')
    message = models.TextField(verbose_name='Pesan')
    is_read = models.BooleanField(default=False, verbose_name='Sudah Dibaca')
    admin_response = models.TextField(blank=True, verbose_name='Respon Admin')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Kritik & Saran'
        verbose_name_plural = 'Kritik & Saran'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_category_display()}: {self.subject[:50]}"


class ActivityLog(models.Model):
    """Model untuk Activity Log Admin"""
    
    class ActionType(models.TextChoices):
        CREATE = 'create', 'Create'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'
        APPROVE = 'approve', 'Approve'
        REJECT = 'reject', 'Reject'
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='activity_logs',
        verbose_name='User'
    )
    action = models.CharField(
        max_length=20, 
        choices=ActionType.choices,
        verbose_name='Aksi'
    )
    model_name = models.CharField(max_length=50, verbose_name='Model')
    object_id = models.PositiveIntegerField(verbose_name='Object ID')
    object_repr = models.CharField(max_length=200, verbose_name='Object')
    changes = models.JSONField(default=dict, blank=True, verbose_name='Perubahan')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP Address')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} - {self.get_action_display()} {self.model_name} ({self.object_repr})"


class PasswordResetToken(models.Model):
    """Model untuk token reset password"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reset_tokens',
        verbose_name='User'
    )
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
    
    def __str__(self):
        return f"Reset token for {self.user.username}"
    
    @property
    def is_valid(self):
        """Check if token is still valid (not expired and not used)"""
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()
    
    @classmethod
    def create_token(cls, user):
        """Create a new reset token for user, invalidating any existing ones"""
        import secrets
        from django.utils import timezone
        from datetime import timedelta
        
        # Invalidate existing tokens
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Create new token (valid for 1 hour)
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=1)
        
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )


class RoomComment(models.Model):
    """Model untuk Komentar dan Rating Ruangan"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='room_comments',
        verbose_name='User'
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Ruangan'
    )
    rating = models.PositiveIntegerField(
        verbose_name='Rating',
        help_text='Rating 1-5 bintang'
    )
    comment = models.TextField(
        verbose_name='Komentar',
        help_text='Komentar tentang ruangan'
    )
    is_approved = models.BooleanField(
        default=True,
        verbose_name='Disetujui'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Komentar Ruangan'
        verbose_name_plural = 'Komentar Ruangan'
        ordering = ['-created_at']
        unique_together = ['user', 'room']  # 1 user hanya bisa 1 komentar per ruangan
    
    def __str__(self):
        return f"{self.user.username} - {self.room.nomor_ruangan} ({self.rating}⭐)"
    
    def save(self, *args, **kwargs):
        # Ensure rating is between 1 and 5
        if self.rating < 1:
            self.rating = 1
        elif self.rating > 5:
            self.rating = 5
        super().save(*args, **kwargs)
        # Update room's average rating
        self.room.update_average_rating()


class RoomReport(models.Model):
    """Model untuk Laporan Ruangan dari User"""
    
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='Ruangan'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='room_reports',
        verbose_name='Pelapor'
    )
    keterangan = models.TextField(
        verbose_name='Keterangan',
        help_text='Deskripsikan masalah atau keluhan terkait ruangan ini'
    )
    is_resolved = models.BooleanField(
        default=False,
        verbose_name='Sudah Ditangani'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Laporan Ruangan'
        verbose_name_plural = 'Laporan Ruangan'
        ordering = ['-created_at']
    
    def __str__(self):
        user_name = self.user.get_full_name() if self.user else 'Anonim'
        return f"Laporan {self.room.nomor_ruangan} oleh {user_name}"
