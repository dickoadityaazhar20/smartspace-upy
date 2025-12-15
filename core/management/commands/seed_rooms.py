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
                'fasilitas': 'AC Central\nProyektor 4K\nSound System\nWiFi High-Speed\nPanggung\nBackdrop LED\nMic Wireless (10)\nPodium',
                'is_active': True,
            },
            {
                'nomor_ruangan': 'Lab Komputer Lt.2',
                'tipe_ruangan': 'Lab',
                'kapasitas': 40,
                'fasilitas': 'AC\nKomputer Core i7 (40 unit)\nProyektor\nWiFi\nWhiteboard\nPrinter',
                'is_active': True,
            },
            {
                'nomor_ruangan': 'Ruang Diskusi 101',
                'tipe_ruangan': 'Kelas',
                'kapasitas': 20,
                'fasilitas': 'AC\nSmart TV 55"\nWiFi\nWhiteboard\nMeja Bundar',
                'is_active': True,
            },
            {
                'nomor_ruangan': 'Lab Multimedia',
                'tipe_ruangan': 'Lab',
                'kapasitas': 30,
                'fasilitas': 'AC\niMac (30 unit)\nGreen Screen\nKamera DSLR\nLighting Studio\nWiFi\nSound Booth',
                'is_active': True,
            },
            {
                'nomor_ruangan': 'Kelas Seminar 305',
                'tipe_ruangan': 'Kelas',
                'kapasitas': 60,
                'fasilitas': 'AC\nProyektor\nWiFi\nMic Wireless\nWhiteboard\nKursi Lipat',
                'is_active': False,  # Sedang renovasi
            },
        ]
        
        for room_data in rooms_data:
            room = Room.objects.create(**room_data)
            self.stdout.write(self.style.SUCCESS(f'  [OK] {room.nomor_ruangan}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nBerhasil menambahkan {len(rooms_data)} ruangan!'))
