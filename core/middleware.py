"""
Custom Middleware for SmartSpace UPY
"""
from django.shortcuts import redirect
from django.conf import settings


class AdminAccessMiddleware:
    """
    Redirect non-staff users to homepage when accessing admin URLs.
    
    This prevents regular users from seeing the admin login form,
    improving security by not exposing the admin interface to non-admin users.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_url = getattr(settings, 'ADMIN_URL', 'smartspace-panel-upy/')
    
    def __call__(self, request):
        # Check if accessing admin URL
        if request.path.startswith(f'/{self.admin_url}'):
            # If user is logged in but not staff, redirect to homepage
            if request.user.is_authenticated and not request.user.is_staff:
                return redirect('home')
        
        return self.get_response(request)
