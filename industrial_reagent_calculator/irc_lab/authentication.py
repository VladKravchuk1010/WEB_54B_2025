from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import redis
from django_redis import get_redis_connection
import time
from django.contrib.auth.models import User

LUA_SCRIPTS = {
    'get_sessions': """
        local pattern = ARGV[1]
        local keys = redis.call('KEYS', pattern)
        local sessions = {}
        for i, key in ipairs(keys) do
            local session_data = redis.call('GET', key)
            if session_data then
                sessions[i] = {key, session_data}
            end
        end
        return sessions
    """,
    
    'create_user_session': """
        local user_id = ARGV[1]
        local username = ARGV[2]
        local session_key = 'user_session:' .. user_id .. ':' .. ARGV[3]
        
        -- Сохраняем сессию на 1 час
        redis.call('SETEX', session_key, 3600, username)
        
        -- Добавляем в набор сессий пользователя
        redis.call('SADD', 'user_sessions:' .. user_id, session_key)
        
        -- Добавляем в общий набор активных сессий
        redis.call('SADD', 'active_sessions', session_key)
        
        return session_key
    """,
    
    'validate_session': """
        local session_key = ARGV[1]
        local username = redis.call('GET', session_key)
        
        if username then
            -- Обновляем TTL
            redis.call('EXPIRE', session_key, 3600)
            return username
        end
        return false
    """,
    
    'delete_user_sessions': """
        local user_id = ARGV[1]
        local session_key_pattern = 'user_session:' .. user_id .. ':*'
        local session_keys = redis.call('KEYS', session_key_pattern)
        
        if #session_keys > 0 then
            redis.call('DEL', unpack(session_keys))
        end
        
        -- Удаляем из набора сессий пользователя
        redis.call('DEL', 'user_sessions:' .. user_id)
        
        -- Удаляем из активных сессий
        for _, key in ipairs(session_keys) do
            redis.call('SREM', 'active_sessions', key)
        end
        
        return #session_keys
    """,
    
    'get_user_sessions': """
        local user_id = ARGV[1]
        local session_keys = redis.call('SMEMBERS', 'user_sessions:' .. user_id)
        local sessions = {}
        
        for i, key in ipairs(session_keys) do
            local username = redis.call('GET', key)
            local ttl = redis.call('TTL', key)
            if username then
                sessions[i] = {key, username, ttl}
            end
        end
        return sessions
    """
}

class LuaSessionAuthentication(BaseAuthentication):
    """
    Кастомная аутентификация через Lua-сессии в Redis
    """
    
    def authenticate(self, request):
        # Получаем session_key из заголовка
        session_key = request.headers.get('X-Session-Key')
        if not session_key:
            return None
        
        try:
            redis_client = get_redis_connection("default")
            validate_session_script = redis_client.register_script(LUA_SCRIPTS['validate_session'])
            username = validate_session_script(keys=[], args=[session_key])
            
            if username and username != False:
                username_str = username.decode('utf-8') if isinstance(username, bytes) else username
                
                # Получаем пользователя
                user = User.objects.filter(username=username_str).first()
                if user:
                    return (user, None)
            
            raise AuthenticationFailed('Недействительная сессия')
            
        except Exception as e:
            raise AuthenticationFailed(f'Ошибка аутентификации: {str(e)}')