import uuid
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.users.models import DomainType, Environment


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient) -> None:
    """
    Тест регистрации нового пользователя.
    
    Args:
        client: HTTP клиент
    """
    user_data = {
        "login": "test@example.com",
        "password": "password123",
        "project_id": str(uuid.uuid4()),
        "env": Environment.PROD.value,
        "domain": DomainType.REGULAR.value
    }
    
    response = await client.post("/api/register", json=user_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["login"] == user_data["login"]
    assert "password" not in data
    assert "id" in data
    assert "created_at" in data
    assert data["locktime"] is None


@pytest.mark.asyncio
async def test_register_duplicate_user(client: AsyncClient) -> None:
    """
    Тест регистрации пользователя с существующим email.
    
    Args:
        client: HTTP клиент
    """
    user_data = {
        "login": "duplicate@example.com",
        "password": "password123",
        "project_id": str(uuid.uuid4()),
        "env": Environment.PROD.value,
        "domain": DomainType.REGULAR.value
    }
    
    response1 = await client.post("/api/register", json=user_data)
    assert response1.status_code == 201
    
    response2 = await client.post("/api/register", json=user_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_user(client: AsyncClient) -> None:
    """
    Тест аутентификации пользователя.
    
    Args:
        client: HTTP клиент
    """
    user_data = {
        "login": "login@example.com",
        "password": "password123",
        "project_id": str(uuid.uuid4()),
        "env": Environment.STAGE.value,
        "domain": DomainType.CANARY.value
    }
    await client.post("/api/register", json=user_data)
    
    login_data = {
        "login": user_data["login"],
        "password": user_data["password"]
    }
    response = await client.post("/api/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    """
    Тест аутентификации с неверным паролем.
    
    Args:
        client: HTTP клиент
    """
    user_data = {
        "login": "wrongpass@example.com",
        "password": "correctpassword",
        "project_id": str(uuid.uuid4()),
        "env": Environment.PROD.value,
        "domain": DomainType.REGULAR.value
    }
    await client.post("/api/register", json=user_data)
    
    login_data = {
        "login": user_data["login"],
        "password": "wrongpassword"
    }
    response = await client.post("/api/login", json=login_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient) -> None:
    """
    Тест получения данных текущего пользователя.
    
    Args:
        client: HTTP клиент
    """
    user_data = {
        "login": "current@example.com",
        "password": "password123",
        "project_id": str(uuid.uuid4()),
        "env": Environment.PREPROD.value,
        "domain": DomainType.REGULAR.value
    }
    await client.post("/api/register", json=user_data)
    
    login_response = await client.post("/api/login", json={
        "login": user_data["login"],
        "password": user_data["password"]
    })
    token = login_response.json()["access_token"]
    
    response = await client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["login"] == user_data["login"]


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient) -> None:
    """
    Тест получения данных без токена.
    
    Args:
        client: HTTP клиент
    """
    response = await client.get("/api/users/me")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_all_users(client: AsyncClient) -> None:
    """
    Тест получения списка всех пользователей.
    
    Args:
        client: HTTP клиент
    """
    users = [
        {
            "login": f"user{i}@example.com",
            "password": "password123",
            "project_id": str(uuid.uuid4()),
            "env": Environment.PROD.value,
            "domain": DomainType.REGULAR.value
        }
        for i in range(3)
    ]
    
    for user in users:
        await client.post("/api/register", json=user)
    
    login_response = await client.post("/api/login", json={
        "login": users[0]["login"],
        "password": users[0]["password"]
    })
    token = login_response.json()["access_token"]
    
    response = await client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_acquire_lock(client: AsyncClient) -> None:
    """
    Тест блокировки пользователя.
    
    Args:
        client: HTTP клиент
    """
    user_data = {
        "login": "lock@example.com",
        "password": "password123",
        "project_id": str(uuid.uuid4()),
        "env": Environment.PROD.value,
        "domain": DomainType.REGULAR.value
    }
    register_response = await client.post("/api/register", json=user_data)
    user_id = register_response.json()["id"]
    
    login_response = await client.post("/api/login", json={
        "login": user_data["login"],
        "password": user_data["password"]
    })
    token = login_response.json()["access_token"]
    
    response = await client.post(
        "/api/users/acquire",
        json={"user_id": user_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["locktime"] is not None


@pytest.mark.asyncio
async def test_acquire_lock_already_locked(client: AsyncClient) -> None:
    """
    Тест блокировки уже заблокированного пользователя.
    
    Args:
        client: HTTP клиент
    """
    user_data = {
        "login": "locked@example.com",
        "password": "password123",
        "project_id": str(uuid.uuid4()),
        "env": Environment.PROD.value,
        "domain": DomainType.REGULAR.value
    }
    register_response = await client.post("/api/register", json=user_data)
    user_id = register_response.json()["id"]
    
    login_response = await client.post("/api/login", json={
        "login": user_data["login"],
        "password": user_data["password"]
    })
    token = login_response.json()["access_token"]
    
    await client.post(
        "/api/users/acquire",
        json={"user_id": user_id},
        headers={"Authorization": f"Bearer {token}"}
    )

    response = await client.post(
        "/api/users/acquire",
        json={"user_id": user_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 423  # Locked


@pytest.mark.asyncio
async def test_release_lock(client: AsyncClient) -> None:
    """
    Тест разблокировки пользователя.
    
    Args:
        client: HTTP клиент
    """
    user_data = {
        "login": "release@example.com",
        "password": "password123",
        "project_id": str(uuid.uuid4()),
        "env": Environment.PROD.value,
        "domain": DomainType.REGULAR.value
    }
    register_response = await client.post("/api/register", json=user_data)
    user_id = register_response.json()["id"]
    
    login_response = await client.post("/api/login", json={
        "login": user_data["login"],
        "password": user_data["password"]
    })
    token = login_response.json()["access_token"]
    
    await client.post(
        "/api/users/acquire",
        json={"user_id": user_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    response = await client.post(
        "/api/users/release",
        json={"user_id": user_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["locktime"] is None


@pytest.mark.asyncio
async def test_release_nonexistent_user(client: AsyncClient) -> None:
    """
    Тест разблокировки несуществующего пользователя.
    
    Args:
        client: HTTP клиент
    """
    user_data = {
        "login": "token@example.com",
        "password": "password123",
        "project_id": str(uuid.uuid4()),
        "env": Environment.PROD.value,
        "domain": DomainType.REGULAR.value
    }
    await client.post("/api/register", json=user_data)
    
    login_response = await client.post("/api/login", json={
        "login": user_data["login"],
        "password": user_data["password"]
    })
    token = login_response.json()["access_token"]
    
    fake_id = str(uuid.uuid4())
    response = await client.post(
        "/api/users/release",
        json={"user_id": fake_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404