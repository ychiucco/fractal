import asyncio
from os import environ

import pytest


@pytest.fixture(scope="session")
async def testserver(tmp_path):
    # cf. https://stackoverflow.com/a/57816608/283972
    import uvicorn
    from fractal_server import start_application
    from multiprocessing import Process

    environ["JWT_SECRET_KEY"] = "secret_key"
    environ["DEPLOYMENT_TYPE"] = "development"
    environ["DATA_DIR_ROOT"] = tmp_path.as_posix()

    environ["DB_ENGINE"] = "sqlite"

    tmp_db_path = tmp_path / "test.db"
    environ["SQLITE_PATH"] = tmp_db_path.as_posix()

    # INIT DB
    from fractal_server.app.db import engine_sync
    from sqlmodel import SQLModel
    import fractal_server.app.models  # noqa: F401

    SQLModel.metadata.create_all(engine_sync)

    # We are explicitly calling start_application() to bypass the task
    # collection routine
    app = start_application()

    config = uvicorn.Config(app, port=10080, log_level="debug")
    server = uvicorn.Server(config)

    def run_server():
        asyncio.run(server.serve())

    proc = Process(target=run_server, args=(), daemon=True)
    proc.start()
    yield environ["FRACTAL_SERVER"]
    proc.kill()


@pytest.fixture()
async def user_factory(client, testserver):
    async def __register_user(email: str, password: str):
        res = await client.post(
            f"{testserver}/auth/register",
            json=dict(email=email, password=password),
        )
        assert res.status_code == 201
        return res.json()

    return __register_user


@pytest.fixture
async def register_user(user_factory):
    return await user_factory(
        email=environ["FRACTAL_USER"], password=environ["FRACTAL_PASSWORD"]
    )
