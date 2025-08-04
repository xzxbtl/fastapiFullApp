from collections import defaultdict
from functools import wraps
from fastapi import HTTPException, Request
from PetProject.src.utils.logs.logs import logger
from time import time


def rate_limit(max_calls: int, time_frame: int):
    """
    Ограничение на количество вызовов для пользователя
    :param max_calls:
    :param time_frame:
    :return:
    """
    def decorator(func):
        calls = defaultdict(list)

        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host
            now = time()

            calls_in_frame = [call for call in calls[client_ip] if call > now - time_frame]
            calls[client_ip] = calls_in_frame

            if len(calls_in_frame) >= max_calls:
                logger.warning(msg=f'Rate Limit Exceeded: {len(calls_in_frame)}, user_id - {client_ip}')
                raise HTTPException(status_code=429, detail="Rate Limit Exceeded.")

            calls[client_ip].append(now)
            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
