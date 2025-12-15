"""
AI Service Module for SmartSpace UPY
Uses Google Gemini API for intelligent room recommendations and chat
"""

import google.generativeai as genai
from django.conf import settings


class GeminiChatService:
    """Service class for interacting with Google Gemini AI"""
    
    def __init__(self):
        # Configure the Gemini API
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Initialize the model - using gemini-flash-latest (works with free tier)
        self.model = genai.GenerativeModel(
            model_name='gemini-flash-latest',
            system_instruction=self._get_system_prompt()
        )
        
        # Chat session storage (in production, use database/cache)
        self.chat_sessions = {}
    
    def _get_system_prompt(self):
        """Generate system prompt with room knowledge"""
        return """Kamu adalah SmartBot, asisten virtual cerdas untuk SmartSpace UPY - platform peminjaman ruangan kampus Universitas PGRI Yogyakarta.

KEPRIBADIAN:
- Ramah, helpful, dan profesional
- Menggunakan bahasa Indonesia yang baik dan sopan
- Responsif dan informatif

KEMAMPUAN UTAMA:
1. Merekomendasikan ruangan sesuai kebutuhan pengguna
2. Menjawab pertanyaan tentang cara peminjaman ruangan
3. Memberikan informasi tentang fasilitas ruangan
4. Membantu troubleshooting masalah peminjaman

INFORMASI PENTING SMARTSPACE UPY:
- Platform peminjaman ruangan gratis untuk civitas akademika UPY
- Proses persetujuan memakan waktu 1x24 jam kerja
- Pembatalan minimal H-1 sebelum tanggal peminjaman
- Ruangan tersedia: Kelas, Laboratorium, dan Aula

INSTRUKSI:
- Jika user membutuhkan rekomendasi ruangan, tanyakan jumlah peserta dan jenis kegiatan
- Selalu sebutkan kapasitas ruangan saat merekomendasikan
- Jika tidak yakin, arahkan user untuk menghubungi admin
- Jawaban singkat dan to-the-point, maksimal 3-4 kalimat
- Gunakan emoji secara wajar untuk membuat percakapan lebih friendly

Jika ada data ruangan yang diberikan dalam format [ROOM_DATA], gunakan informasi tersebut untuk memberikan rekomendasi yang akurat."""

    def get_available_rooms(self, min_capacity=0, room_type=None):
        """Get available rooms from database"""
        # Lazy import to avoid circular imports
        from core.models import Room
        
        queryset = Room.objects.filter(is_active=True)
        
        if min_capacity > 0:
            queryset = queryset.filter(kapasitas__gte=min_capacity)
        
        if room_type:
            queryset = queryset.filter(tipe_ruangan__iexact=room_type)
        
        rooms = queryset.order_by('kapasitas')[:5]
        
        room_info = []
        for room in rooms:
            room_info.append(f"- {room.nomor_ruangan} ({room.get_tipe_ruangan_display()}, kapasitas {room.kapasitas} orang)")
        
        return room_info
    
    def _extract_room_context(self, message):
        """Extract room-related context from user message"""
        context_parts = []
        
        # Check for capacity mentions
        import re
        capacity_match = re.search(r'(\d+)\s*orang', message.lower())
        min_capacity = int(capacity_match.group(1)) if capacity_match else 0
        
        # Check for room type mentions
        room_type = None
        if 'lab' in message.lower() or 'laboratorium' in message.lower():
            room_type = 'Lab'
        elif 'aula' in message.lower():
            room_type = 'Aula'
        elif 'kelas' in message.lower():
            room_type = 'Kelas'
        
        # Get matching rooms if capacity or type mentioned
        if min_capacity > 0 or room_type:
            try:
                rooms = self.get_available_rooms(min_capacity, room_type)
                if rooms:
                    context_parts.append(f"\n[ROOM_DATA] Ruangan yang tersedia dan sesuai kriteria:\n" + "\n".join(rooms))
            except Exception as e:
                print(f"Error getting rooms: {e}")
        
        return "".join(context_parts)
    
    def chat(self, session_id, user_message):
        """Send a message and get AI response"""
        try:
            # Get or create chat session
            if session_id not in self.chat_sessions:
                self.chat_sessions[session_id] = self.model.start_chat(history=[])
            
            chat = self.chat_sessions[session_id]
            
            # Add room context if relevant
            room_context = self._extract_room_context(user_message)
            enhanced_message = user_message + room_context
            
            # Get response from Gemini
            response = chat.send_message(enhanced_message)
            
            return {
                'success': True,
                'response': response.text
            }
            
        except Exception as e:
            import traceback
            print(f"AI Chat Error: {e}")
            print(traceback.format_exc())
            return {
                'success': False,
                'error': str(e),
                'response': f'Maaf, terjadi kesalahan: {str(e)[:100]}. Silakan coba lagi.'
            }
    
    def clear_session(self, session_id):
        """Clear chat session"""
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]


# Singleton instance
_chat_service = None

def get_chat_service():
    """Get or create singleton chat service instance"""
    global _chat_service
    if _chat_service is None:
        _chat_service = GeminiChatService()
    return _chat_service
