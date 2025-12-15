from django.core.management.base import BaseCommand
from core.models import User


class Command(BaseCommand):
    help = 'Setup admin superuser untuk akses Django Admin'

    def handle(self, *args, **options):
        username = 'admin'
        email = 'admin@example.com'
        password = 'admin123'
        
        # Cek apakah user admin sudah ada
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Superuser "{username}" sudah ada!')
            )
        else:
            # Buat superuser baru
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                role='Admin'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Superuser created: {username} / {password}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Akses admin panel di: http://127.0.0.1:8000/admin/')
            )
