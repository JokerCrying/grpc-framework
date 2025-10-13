import unittest
from src.grpc_framework.core import rpc, Service
from src.grpc_framework.core.enums import Interaction


class UserService(Service):
    @rpc(Interaction.unary, Interaction.unary)
    async def create_user(self):
        pass

    @rpc(Interaction.unary, Interaction.unary)
    async def user_list(self):
        pass


class TestCBV(unittest.TestCase):
    def test_cbv(self):
        print(UserService.collect_rpc_methods())
