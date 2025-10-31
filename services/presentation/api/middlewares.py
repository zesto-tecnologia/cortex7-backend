from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from services.presentation.utils.get_env import get_can_change_keys_env
from services.presentation.utils.user_config import update_env_with_user_config


class UserConfigEnvUpdateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            if get_can_change_keys_env() != "false":
                update_env_with_user_config()
        except Exception as e:
            # Log the error but don't block the request
            print(f"Warning: Failed to update user config: {e}")
        return await call_next(request)
