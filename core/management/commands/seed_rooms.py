from django.core.management.base import BaseCommand
from core.models import Room


class Command(BaseCommand):
    help = 'Seed database dengan data dummy ruangan'

    def handle(self, *args, **options):
        self.stdout.write('Menambahkan data dummy ruangan...')
        
        # Hapus data lama (opsional)
        Room.objects.all().delete()
        
        rooms_data = [
            {
                'nomor_ruangan': 'Aula Utama Gedung A',
                'tipe_ruangan': 'Aula',
                'kapasitas': 500,
                'fasilitas': ['AC Central', 'Proyektor 4K', 'Sound System', 'WiFi High-Speed', 'Panggung', 'Backdrop LED', 'Mic Wireless (10)', 'Podium'],
                'is_active': True,
            },
            {
                'nomor_ruangan': 'Lab Komputer Lt.2',
                'tipe_ruangan': 'Lab',
                'kapasitas': 40,
                'fasilitas': ['AC', 'Komputer Core i7 (40 unit)', 'Proyektor', 'WiFi', 'Whiteboard', 'Printer'],
                'is_active': True,
            },
            {
                'nomor_ruangan': 'Ruang Diskusi 101',
                'tipe_ruangan': 'Kelas',
                'kapasitas': 20,
                'fasilitas': ['AC', 'Smart TV 55"', 'WiFi', 'Whiteboard', 'Meja Bundar'],
                'is_active': True,
            },
            {
                'nomor_ruangan': 'Lab Multimedia',
                'tipe_ruangan': 'Lab',
                'kapasitas': 30,
                'fasilitas': ['AC', 'iMac (30 unit)', 'Green Screen', 'Kamera DSLR', 'Lighting Studio', 'WiFi', 'Sound Booth'],
                'is_active': True,
            },
            {
                'nomor_ruangan': 'Kelas Seminar 305',
                'tipe_ruangan': 'Kelas',
                'kapasitas': 60,
                'fasilitas': ['AC', 'Proyektor', 'WiFi', 'Mic Wireless', 'Whiteboard', 'Kursi Lipat'],
                'is_active': False,  # Sedang renovasi
            },
        ]
        
        for room_data in rooms_data:
            room = Room.objects.create(**room_data)
            self.stdout.write(self.style.SUCCESS(f'  [OK] {room.nomor_ruangan}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nBerhasil menambahkan {len(rooms_data)} ruangan!'))
