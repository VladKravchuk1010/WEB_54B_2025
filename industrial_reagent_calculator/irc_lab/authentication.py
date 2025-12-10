from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django_redis import get_redis_connection
import time
from django.contrib.auth.models import User

# константа времени жизни сессии (1 час)
SESSION_TTL = 3600

# создать сессию
def create_user_session(user_id, username):
    redis_conn = get_redis_connection("default")
    
    # Генерируем уникальный ключ
    timestamp = int(time.time())
    session_key = f"session:{user_id}:{timestamp}"
    
    # LUA СКРИПТ:
    # 1. Записываем данные в Hash (HMSET)
    # 2. Ставим таймер удаления (EXPIRE)
    # KEYS[1] - это session_key
    # ARGV[1] - user_id, ARGV[2] - username, ARGV[3] - timestamp, ARGV[4] - TTL
    lua_script = """
        redis.call('HMSET', KEYS[1], 
            'user_id', ARGV[1], 
            'username', ARGV[2], 
            'created_at', ARGV[3]
        )
        redis.call('EXPIRE', KEYS[1], ARGV[4])
        return KEYS[1]
    """
    
    # Выполняем скрипт (1 ключ, остальные аргументы)
    redis_conn.eval(lua_script, 1, session_key, user_id, username, timestamp, SESSION_TTL)
    
    return session_key

# проверка сессии
def get_session_user(session_key):
    redis_conn = get_redis_connection("default")
    
    # LUA СКРИПТ:
    # 1. Проверяем, существует ли ключ (EXISTS)
    # 2. Если да - обновляем таймер (EXPIRE) и возвращаем имя (HGET)
    # KEYS[1] - session_key
    # ARGV[1] - TTL
    lua_script = """
        if redis.call('EXISTS', KEYS[1]) == 1 then
            redis.call('EXPIRE', KEYS[1], ARGV[1])
            return redis.call('HGET', KEYS[1], 'username')
        else
            return nil
        end
    """
    
    username = redis_conn.eval(lua_script, 1, session_key, SESSION_TTL)
    
    # Redis возвращает bytes, декодируем
    if username:
        return username.decode('utf-8')
    return None

# удаление сессии
def destroy_session(session_key):
    redis_conn = get_redis_connection("default")
    
    # LUA СКРИПТ:
    # Просто удаляем ключ
    lua_script = "return redis.call('DEL', KEYS[1])"
    
    return redis_conn.eval(lua_script, 1, session_key)


class LuaSessionAuthentication(BaseAuthentication):
    def authenticate(self, request):
        session_key = request.headers.get('X-Session-Key')
        
        if not session_key:
            return None

        username = get_session_user(session_key)

        if not username:
            raise AuthenticationFailed('Сессия недействительна или истекла')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise AuthenticationFailed('Пользователь не найден')

        return (user, None)