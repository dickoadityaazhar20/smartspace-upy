"""
Management command to create superadmin users
Usage: python manage.py create_superadmin
"""
from django.core.management.base import BaseCommand
from core.models import User


class Command(BaseCommand):
    help = 'Create superadmin users for SmartSpace UPY'

    def handle(self, *args, **options):
        superadmins = [
            {
                'username': 'admin',
                'email': 'admin@smartspace.upy.ac.id',
                'password': 'Admin@123',
                'first_name': 'Admin',
                'last_name': 'SmartSpace',
                'npm_nip': 'ADMIN001',
                'role': 'Admin',
            },
            {
                'username': 'superadmin',
                'email': 'superadmin@smartspace.upy.ac.id',
                'password': 'Super@123',
                'first_name': 'Super',
                'last_name': 'Admin',
                'npm_nip': 'ADMIN002',
                'role': 'Admin',
            },
        ]

        for admin_data in superadmins:
            username = admin_data['username']
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'User "{username}" already exists, skipping...'))
                continue
            
            # Create superuser
            user = User.objects.create_superuser(
                username=admin_data['username'],
                email=admin_data['email'],
                password=admin_data['password'],
            )
            
            # Update additional fields
            user.first_name = admin_data['first_name']
            user.last_name = admin_data['last_name']
            user.npm_nip = admin_data['npm_nip']
            user.role = admin_data['role']
            user.save()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Superadmin "{username}" created successfully!'))
            self.stdout.write(f'   Email: {admin_data["email"]}')
            self.stdout.write(f'   Password: {admin_data["password"]}')
            self.stdout.write('')

        self.stdout.write(self.style.SUCCESS('\n🎉 Done! You can now login to admin panel.'))
