from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateFilter
from unfold.decorators import action, display
from .models import User, Room, Booking
from .email_utils import send_booking_approved_email, send_booking_rejected_email


# Custom User Admin - Enhanced for SmartSpace UPY with Unfold
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = ('npm_nip', 'get_full_name', 'email', 'fakultas', 'program_studi', 'angkatan', 'nomor_hp', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'fakultas', 'program_studi', 'angkatan', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'npm_nip', 'first_name', 'last_name', 'fakultas', 'program_studi', 'nomor_hp')
    ordering = ('-date_joined',)
    list_per_page = 25
    
    # Fieldsets for detailed view
    fieldsets = (
        ('Akun', {'fields': ('username', 'password')}),
        ('Informasi Pribadi', {'fields': ('first_name', 'last_name', 'email')}),
        ('Data Mahasiswa/Dosen', {
            'fields': ('npm_nip', 'fakultas', 'program_studi', 'angkatan', 'nomor_hp', 'role'),
            'classes': ('wide',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    # Fields shown when adding new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Data Lengkap', {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email', 'npm_nip', 'fakultas', 'program_studi', 'angkatan', 'nomor_hp', 'role'),
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username
    get_full_name.short_description = 'Nama Lengkap'
    
    def get_search_results(self, request, queryset, search_term):
        """Override to search by first_name only using 'starts with'"""
        if not search_term:
            return queryset, False
        
        # Search by first_name only starting with search term
        queryset = queryset.filter(first_name__istartswith=search_term)
        return queryset, False


# Room Admin with Unfold
@admin.register(Room)
class RoomAdmin(ModelAdmin):
    list_display = ('nomor_ruangan', 'tipe_ruangan', 'kapasitas', 'is_active', 'created_at')
    list_filter = ('tipe_ruangan', 'is_active')
    search_fields = ('nomor_ruangan',)
    ordering = ('nomor_ruangan',)
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Informasi Ruangan', {
            'fields': ('nomor_ruangan', 'tipe_ruangan', 'kapasitas')
        }),
        ('Detail & Fasilitas', {
            'fields': ('fasilitas', 'foto_ruangan', 'is_active')
        }),
        ('Deskripsi Ruangan', {
            'fields': ('deskripsi',),
            'description': 'Isi deskripsi lengkap tentang ruangan ini'
        }),
        ('Peraturan Penggunaan', {
            'fields': ('peraturan', 'larangan'),
            'description': '✅ Hal yang Diperbolehkan: isi peraturan yang boleh dilakukan (satu per baris). ❌ Hal yang Dilarang: isi larangan yang tidak boleh dilakukan (satu per baris).'
        }),
    )
    
    def get_search_results(self, request, queryset, search_term):
        """Override to search by room name using 'starts with'"""
        if not search_term:
            return queryset, False
        
        # Search by nomor_ruangan (nama ruangan) starting with search term
        queryset = queryset.filter(nomor_ruangan__istartswith=search_term)
        return queryset, False


# Booking Admin Actions
@admin.action(description='✅ Approve peminjaman terpilih')
def make_approved(modeladmin, request, queryset):
    updated = queryset.update(status='Approved')
    # Send email notifications
    for booking in queryset:
        try:
            send_booking_approved_email(booking)
        except Exception as e:
            print(f"Failed to send approval email: {e}")
    modeladmin.message_user(request, f'{updated} peminjaman berhasil di-approve. Email notifikasi telah dikirim.')


@admin.action(description='❌ Reject peminjaman terpilih')
def make_rejected(modeladmin, request, queryset):
    updated = queryset.update(status='Rejected')
    # Send email notifications
    for booking in queryset:
        try:
            send_booking_rejected_email(booking)
        except Exception as e:
            print(f"Failed to send rejection email: {e}")
    modeladmin.message_user(request, f'{updated} peminjaman berhasil di-reject. Email notifikasi telah dikirim.')


@admin.action(description='⏳ Set Pending')
def make_pending(modeladmin, request, queryset):
    updated = queryset.update(status='Pending')
    modeladmin.message_user(request, f'{updated} peminjaman di-set ke Pending.')


@admin.action(description='🔄 Set On Process')
def make_on_process(modeladmin, request, queryset):
    updated = queryset.update(status='On Process')
    modeladmin.message_user(request, f'{updated} peminjaman di-set ke On Process.')


# Booking Admin - Enhanced with Unfold
@admin.register(Booking)
class BookingAdmin(ModelAdmin):
    list_display = ('id', 'get_user_npm', 'get_user_name', 'get_user_fakultas', 'get_user_prodi', 'get_user_angkatan', 'room', 'jumlah_tamu', 'get_tanggal_mulai', 'get_tanggal_selesai', 'keperluan', 'status', 'get_document_link')
    list_filter = ('status', 'tanggal_mulai', 'room__tipe_ruangan', 'user__fakultas', 'created_at')
    search_fields = ('user__npm_nip', 'user__first_name', 'user__last_name', 'room__nomor_ruangan', 'keperluan')
    ordering = ('-created_at',)
    date_hierarchy = 'tanggal_mulai'
    list_per_page = 25
    actions = [make_approved, make_rejected, make_pending, make_on_process]
    
    # User info display methods
    def get_user_npm(self, obj):
        return obj.user.npm_nip if obj.user else '-'
    get_user_npm.short_description = 'NPM/NIP'
    get_user_npm.admin_order_field = 'user__npm_nip'
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() if obj.user else '-'
    get_user_name.short_description = 'Nama Peminjam'
    get_user_name.admin_order_field = 'user__first_name'
    
    def get_user_fakultas(self, obj):
        return obj.user.fakultas if obj.user and obj.user.fakultas else '-'
    get_user_fakultas.short_description = 'Fakultas'
    get_user_fakultas.admin_order_field = 'user__fakultas'
    
    def get_user_prodi(self, obj):
        return obj.user.program_studi if obj.user and obj.user.program_studi else '-'
    get_user_prodi.short_description = 'Program Studi'
    get_user_prodi.admin_order_field = 'user__program_studi'
    
    def get_user_angkatan(self, obj):
        return obj.user.angkatan if obj.user and obj.user.angkatan else '-'
    get_user_angkatan.short_description = 'Angkatan'
    get_user_angkatan.admin_order_field = 'user__angkatan'
    
    # Custom datetime display with 24-hour format
    def get_tanggal_mulai(self, obj):
        from django.utils import timezone
        local_time = timezone.localtime(obj.tanggal_mulai)
        return local_time.strftime('%d %b %Y, %H:%M')
    get_tanggal_mulai.short_description = 'Tanggal Mulai'
    get_tanggal_mulai.admin_order_field = 'tanggal_mulai'
    
    def get_tanggal_selesai(self, obj):
        from django.utils import timezone
        local_time = timezone.localtime(obj.tanggal_selesai)
        return local_time.strftime('%d %b %Y, %H:%M')
    get_tanggal_selesai.short_description = 'Tanggal Selesai'
    get_tanggal_selesai.admin_order_field = 'tanggal_selesai'
    
    def get_created_at(self, obj):
        from django.utils import timezone
        local_time = timezone.localtime(obj.created_at)
        return local_time.strftime('%d %b %Y, %H:%M')
    get_created_at.short_description = 'Created at'
    get_created_at.admin_order_field = 'created_at'
    
    def get_document_link(self, obj):
        from django.utils.html import format_html
        if obj.dokumen_pendukung:
            return format_html(
                '<a href="{}" target="_blank" style="color: #ec4899; text-decoration: underline;">📄 Download</a>',
                obj.dokumen_pendukung.url
            )
        return '-'
    get_document_link.short_description = 'Dokumen'
    get_document_link.allow_tags = True
    
    fieldsets = (
        ('Peminjam', {
            'fields': ('user',),
        }),
        ('Detail Peminjaman', {
            'fields': ('room', 'jumlah_tamu', 'tanggal_mulai', 'tanggal_selesai', 'keperluan'),
        }),
        ('Dokumen Pendukung', {
            'fields': ('dokumen_pendukung',),
        }),
        ('Status', {
            'fields': ('status',),
        }),
    )
    
    # Read-only for dates
    readonly_fields = ('created_at', 'updated_at')
    
    def get_search_results(self, request, queryset, search_term):
        """Override to search by user's first_name using 'starts with'"""
        if not search_term:
            return queryset, False
        
        # Search by user's first_name starting with search term
        queryset = queryset.filter(user__first_name__istartswith=search_term)
        return queryset, False


# Wishlist Admin with Unfold
from .models import Wishlist, Message

@admin.register(Wishlist)
class WishlistAdmin(ModelAdmin):
    list_display = ('user', 'room', 'created_at')
    list_filter = ('created_at', 'room__tipe_ruangan')
    search_fields = ('user__npm_nip', 'user__first_name', 'room__nomor_ruangan')
    ordering = ('-created_at',)


# Message Admin removed - Using custom Chat User interface instead
# The Message model is managed through /admin/chat/ with WhatsApp-style UI


# Testimonial Admin with Unfold - CMS for Homepage Testimonials
from .models import Testimonial

@admin.register(Testimonial)
class TestimonialAdmin(ModelAdmin):
    list_display = ('nama', 'role', 'rating', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'rating', 'created_at')
    search_fields = ('nama', 'role', 'content')
    ordering = ('order', '-created_at')
    list_editable = ('is_active', 'order', 'rating')
    list_per_page = 20
    
    fieldsets = (
        ('Informasi Pengguna', {
            'fields': ('nama', 'role', 'foto'),
            'description': 'Data orang yang memberikan testimoni'
        }),
        ('Testimoni', {
            'fields': ('content', 'rating'),
            'description': 'Isi testimoni dan rating (1-5 bintang)'
        }),
        ('Pengaturan Tampilan', {
            'fields': ('is_active', 'order'),
            'description': 'Aktifkan untuk menampilkan di homepage. Urutan kecil tampil duluan.'
        }),
    )
