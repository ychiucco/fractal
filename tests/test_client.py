from os import environ

import httpx
from devtools import debug

from fractal import __VERSION__


DEFAULT_TEST_EMAIL = environ["FRACTAL_USER"]


async def test_version(invoke, testserver):
    iface = await invoke("version")
    debug(iface.data)
    assert f"version: {__VERSION__}" in iface.data
    assert iface.retcode == 0


async def test_server(testserver):
    """
    GIVEN a testserver
    WHEN it gets called
    THEN it replies
    """
    res = httpx.get("http://localhost:10080/api/alive/")
    debug(res.json())
    assert res.status_code == 200


async def test_user(clear_db, register_user):
    debug(register_user)
    assert register_user["email"] == DEFAULT_TEST_EMAIL


async def test_user_override(clear_db, testserver, user_factory, invoke):
    """
    GIVEN a user whose credentials differ from those of the environment
    WHEN the client is invoked with -u and -p
    THEN the credentials are overridden
    """
    EMAIL = "other_user@exact-lab.it"
    PASSWORD = "other_password"
    await user_factory(email=EMAIL, password=PASSWORD)

    res = await invoke(f"-u {EMAIL} -p {PASSWORD} project list")
    assert res.retcode == 0


async def test_bad_credentials(clear_db, testserver, invoke):
    """
    GIVEN a registered user
    WHEN wrong credentials are passed
    THEN the client returns an error
    """
    res = await invoke("-u nouser@exact-lab.it -p nopassword project list")
    res.show()
    assert res.retcode != 0
    assert "BAD_CREDENTIALS" in res.data
