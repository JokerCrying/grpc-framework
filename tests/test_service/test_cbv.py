import unittest
from src.grpc_framework.core import rpc, Service, unary_unary, unary_stream, stream_unary, stream_stream
from src.grpc_framework.core.enums import Interaction


class UserService(Service):
    @rpc(Interaction.unary, Interaction.unary)
    async def create_user(self):
        pass

    @rpc(Interaction.unary, Interaction.unary)
    async def user_list(self):
        pass

    @unary_unary
    async def uu(self):
        pass

    @unary_stream
    async def us(self):
        pass

    @stream_unary
    async def su(self):
        pass

    @stream_stream
    async def ss(self):
        pass


class TestCBV(unittest.TestCase):
    def test_cbv(self):
        print(UserService.collect_rpc_methods())
