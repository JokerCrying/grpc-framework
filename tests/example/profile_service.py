import uuid
from dataclasses import dataclass
from src.grpc_framework import Service

service = Service('ProfileService')


@dataclass
class Profile:
    name: str


@service.unary_unary
async def get_profile():
    return Profile(name=str(uuid.uuid4()))
