from pathlib import Path

import jwt
from httpx import AsyncClient
from jwt.exceptions import ExpiredSignatureError

from .config import settings


class AuthenticationError(ValueError):
    pass


class AuthToken:
    def __init__(self, client: AsyncClient):
        self.client = client

        try:
            with open(settings.SESSION_CACHE_PATH, "r") as f:
                self.token = f.read()
        except FileNotFoundError:
            pass

    async def _get_fresh_token(self):
        data = dict(
            username=settings.FRACTAL_USER,
            password=settings.FRACTAL_PASSWORD,
        )
        res = await self.client.post(
            f"{settings.FRACTAL_SERVER}/auth/token/login", data=data
        )
        if res.status_code != 200:
            raise AuthenticationError(
                "Error: could not obtain token. Is the user registered?\n"
                f"{res.json()}\n"
            )
        raw_token = res.json()
        self.token = raw_token["access_token"]
        with open(Path(settings.SESSION_CACHE_PATH).expanduser(), "w") as f:
            f.write(self.token)

    @property
    def expired(self):
        try:
            jwt.decode(
                jwt=self.token,
                requires=["exp"],
                options={
                    "verify_signature": False,
                    "verify_exp": True,
                },
            )
            return False
        except AttributeError:
            return True
        except ExpiredSignatureError:
            return True

    async def header(self):
        token = await self.__call__()
        return dict(Authorization=f"Bearer {token}")

    async def __call__(self):
        if self.expired:
            await self._get_fresh_token()
        return self.token


class AuthClient:
    def __init__(self):
        self.auth = None
        self.client = None

    async def __aenter__(self):
        self.client = AsyncClient()
        self.auth = AuthToken(client=self.client)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.client.aclose()

    async def get(self, *args, **kwargs):
        return await self.client.get(
            headers=await self.auth.header(), *args, **kwargs
        )
