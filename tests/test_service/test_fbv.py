import unittest
from src.grpc_framework.core import rpc, Service
from src.grpc_framework.core.enums import Interaction

user_service = Service('UserService')


@user_service.method(Interaction.unary, Interaction.unary)
async def create_user():
    pass


@user_service.method(Interaction.unary, Interaction.unary)
async def user_list():
    pass


class TestFBV(unittest.TestCase):
    def test_fbv(self):
        print(user_service.methods)
