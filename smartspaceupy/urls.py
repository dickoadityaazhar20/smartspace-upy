"""
URL configuration for smartspaceupy project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.admin_views import chat_list_view, chat_detail_view, chat_send_view, chat_delete_view, chat_delete_conversation_view, chat_poll_view, chat_pin_view, admin_shortcuts_view, admin_dashboard_stats

# Add custom admin URLs to admin.site
admin.site.get_urls_original = admin.site.get_urls

def custom_admin_urls():
    custom_urls = [
        path('api/stats/', admin_dashboard_stats, name='admin_dashboard_stats'),
        path('shortcuts/', admin_shortcuts_view, name='admin_shortcuts'),
        path('chat/', chat_list_view, name='chat_list'),
        path('chat/<int:user_id>/', chat_detail_view, name='chat_detail'),
        path('chat/<int:user_id>/poll/', chat_poll_view, name='chat_poll'),
        path('chat/send/', chat_send_view, name='chat_send'),
        path('chat/delete/', chat_delete_view, name='chat_delete'),
        path('chat/delete-conversation/', chat_delete_conversation_view, name='chat_delete_conversation'),
        path('chat/pin/', chat_pin_view, name='chat_pin'),
    ]
    return custom_urls + admin.site.get_urls_original()

admin.site.get_urls = custom_admin_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
