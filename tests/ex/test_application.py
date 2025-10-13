import unittest
from src.grpc_framework.application import GRPCFramework
from src.grpc_framework.config import GRPCFrameworkConfig


class TestApplication(unittest.TestCase):
    def test_application_create(self):
        config = GRPCFrameworkConfig()
        app = GRPCFramework(config=config)
        print('config ===', config)
        print('application ===', app)
