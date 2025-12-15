from django.urls import path
from . import views, admin_views

urlpatterns = [
    path('', views.home, name='home'),
    path('rooms/', views.rooms_list, name='rooms_list'),
    path('room/<int:pk>/', views.room_detail, name='room_detail'),
    path('dashboard/', views.user_dashboard, name='dashboard'),
    
    # User Pages
    path('profile/', views.profile_page, name='profile'),
    path('wishlist/', views.wishlist_page, name='wishlist'),
    path('messages/', views.messages_page, name='messages'),
    
    # Auth API endpoints
    path('api/register/', views.api_register, name='api_register'),
    path('api/login/', views.api_login, name='api_login'),
    path('api/logout/', views.api_logout, name='api_logout'),
    path('api/check-auth/', views.api_check_auth, name='api_check_auth'),
    
    # Password Reset
    path('api/forgot-password/', views.api_forgot_password, name='api_forgot_password'),
    path('api/reset-password/', views.api_reset_password, name='api_reset_password'),
    path('reset-password/<str:token>/', views.reset_password_page, name='reset_password_page'),
    
    # Wishlist API
    path('api/wishlist/toggle/', views.api_wishlist_toggle, name='api_wishlist_toggle'),
    path('api/wishlist/list/', views.api_wishlist_list, name='api_wishlist_list'),
    path('api/wishlist/check/<int:room_id>/', views.api_wishlist_check, name='api_wishlist_check'),
    
    # Profile API
    path('api/profile/', views.api_profile_get, name='api_profile_get'),
    path('api/profile/update/', views.api_profile_update, name='api_profile_update'),
    
    # Messages API
    path('api/messages/', views.api_messages_list, name='api_messages_list'),
    path('api/messages/count/', views.api_messages_count, name='api_messages_count'),
    path('api/messages/poll/', views.api_messages_poll, name='api_messages_poll'),
    path('api/messages/read/<int:message_id>/', views.api_message_read, name='api_message_read'),
    path('api/messages/send/', views.api_send_message, name='api_send_message'),
    
    # Booking API
    path('api/booking/cancel/', views.api_booking_cancel, name='api_booking_cancel'),
    
    # Calendar & Conflict Detection API
    path('api/calendar/<int:room_id>/', views.api_calendar_bookings, name='api_calendar_bookings'),
    path('api/bookings/check-conflict/', views.api_check_booking_conflict, name='api_check_booking_conflict'),
    path('api/booked-slots/<int:room_id>/<str:date_str>/', views.api_booked_slots, name='api_booked_slots'),
    
    # AI Chat API
    path('api/chat/', views.api_chat, name='api_chat'),
    
    # Feedback API (Kritik & Saran)
    path('feedback/', views.feedback_page, name='feedback'),
    path('api/feedback/submit/', views.api_feedback_submit, name='api_feedback_submit'),
]

