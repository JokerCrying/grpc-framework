import uuid
import random
import asyncio
from dataclasses import dataclass
from src.grpc_framework import Service, unary_unary, unary_stream


@dataclass
class User:
    id: int
    name: str


@dataclass
class UserCreate:
    name: str


class UserService(Service):
    @unary_unary
    async def create_user(self, request: UserCreate):
        await asyncio.sleep(0.1)  # Simulated IO operation
        return User(id=random.randint(1, 9999), name=request.name)

    @unary_stream
    async def iter_user(self):
        for i in range(1, 11):
            yield User(
                id=i,
                name=str(uuid.uuid4())
            )
