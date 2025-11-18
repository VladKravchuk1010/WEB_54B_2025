from django_redis import get_redis_connection
from .authentication import LUA_SCRIPTS
from django.contrib.auth.models import User

from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser

class LuaSessionMiddleware(MiddlewareMixin):
    """
    Middleware для автоматической аутентификации через Lua-сессии
    """
    
    def process_request(self, request):
        # Для API requests проверяем Lua-сессию
        if request.path.startswith('/api/'):
            session_key = request.headers.get('X-Session-Key')
            if session_key:
                try:
                    redis_client = get_redis_connection("default")
                    validate_session_script = redis_client.register_script(LUA_SCRIPTS['validate_session'])
                    username = validate_session_script(keys=[], args=[session_key])
                    
                    if username and username != False:
                        username_str = username.decode('utf-8') if isinstance(username, bytes) else username
                        user = User.objects.filter(username=username_str).first()
                        if user:
                            request.user = user
                            request.session_key = session_key
                            return
                
                except Exception as e:
                    print(f"Lua session middleware error: {e}")
            
            # Если сессия невалидна - анонимный пользователь
            request.user = AnonymousUser()