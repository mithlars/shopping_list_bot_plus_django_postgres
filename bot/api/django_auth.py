import asyncio
import requests
from functools import wraps
from bot.constants import DJANGO_USERNAME, DJANGO_USER_PASSWORD
from bot.constants import django_login_url


class MySession(requests.Session):
    """
        Class needs to fix adding csrf-token to request's cookies
    """

    async def add_csrftoken_to_headers(self, **kwargs):
        csrftoken = self.cookies.get("csrftoken")
        if csrftoken is not None and csrftoken != "":
            kwargs.setdefault("headers", {})
            if not kwargs["headers"].get("X-CSRFToken"):
                kwargs["headers"]["X-CSRFToken"] = csrftoken

        return kwargs

    async def post(self, url, data=None, json=None, **kwargs):
        kwargs = await self.add_csrftoken_to_headers(**kwargs)
        return self.request("POST", url, data=data, json=json, **kwargs)

    async def put(self, url, data=None, **kwargs):
        kwargs = await self.add_csrftoken_to_headers(**kwargs)
        return self.request("PUT", url, data=data, **kwargs)

    async def patch(self, url, data=None, **kwargs):
        kwargs = await self.add_csrftoken_to_headers(**kwargs)
        return self.request("PATCH", url, data=data, **kwargs)

    async def delete(self, url, **kwargs):
        kwargs = await self.add_csrftoken_to_headers(**kwargs)
        return self.request("DELETE", url, **kwargs)


class DjangoAuth:

    def __init__(self, api_login_url):
        self.api_login_url = api_login_url
        self.session = MySession()
        self.last_request_time = None

    async def login(self):
        """Method performs authorisation on Django service"""

        # Делаем get-запрос для получения csrf-токена:
        self.session.get(self.api_login_url)
        # if 'csrftoken' in self.session.cookies:
        #     self.session.headers.update({'X-CSRFToken': self.session.cookies['csrftoken']})

        # Делаем login-запрос:
        login_data = {
            'username': DJANGO_USERNAME,
            'password': DJANGO_USER_PASSWORD,
        }
        response = await self.session.post(self.api_login_url, data=login_data)
        # Если login-запрос удался -- обновляем время последнего запроса:
        f = open('logs_main.txt', 'a')
        if response.status_code == 200:
            self.last_request_time = asyncio.get_event_loop().time()
            f.write('Login is OK')
            f.close()
            print('Login is OK')
            return True
        else:
            f.write('Login is failed')
            f.close()
            print('Login is failed')
            return False

    async def refresh_session(self):
        """Method refreshes session in 270 seconds after last request"""
        while True:
            if (self.last_request_time and
                    asyncio.get_event_loop().time() - self.last_request_time > 270):
                response = self.session.get(self.api_login_url)
                self.last_request_time = asyncio.get_event_loop().time()
                if response.status_code == 401:
                    await self.login()
            await asyncio.sleep(200)  # Проверяем каждую секунду


django_auth = DjangoAuth(django_login_url)


# Decorator for updating user's last activity time:
def update_last_request_time(django_auth_obj: DjangoAuth):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            django_auth_obj.last_request_time = asyncio.get_event_loop().time()
            return result

        return wrapper

    return decorator
