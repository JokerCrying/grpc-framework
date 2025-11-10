import unittest
import inspect
from src.grpc_framework.core.adaptor import GRPCAdaptor
from src.grpc_framework.application import GRPCFramework
from src.grpc_framework.config import GRPCFrameworkConfig
from src.grpc_framework.core.enums import Interaction
from src.grpc_framework.core.service import Service


class CheckFuncType(unittest.TestCase):
    def setUp(self):
        self.app = GRPCFramework(config=GRPCFrameworkConfig(package='test'))
        self.adaptor = GRPCAdaptor(self.app)

    def test_func_type(self):
        func = self.adaptor.wrap_unary_unary_handler({
            'handler': lambda x: x,
            'request_interaction': Interaction.unary,
            'response_interaction': Interaction.unary,
            'rpc_service': Service(),
            'input_param_info': {},
            'return_param_info': None
        })

        async def coro(): pass

        def normal(): pass

        self.assertIs(inspect.iscoroutinefunction(func), True)
        self.assertIs(inspect.iscoroutinefunction(coro), True)
        self.assertIs(inspect.iscoroutinefunction(normal), False)
