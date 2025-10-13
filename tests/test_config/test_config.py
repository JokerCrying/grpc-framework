import unittest
from src.grpc_framework.config import GRPCFrameworkConfig


class TestConfig(unittest.TestCase):

    def test_from_module(self):
        config = GRPCFrameworkConfig.from_module('tests.test_config.config')
        print('config ===', config)

    def test_from_yaml(self):
        config = GRPCFrameworkConfig.from_file('tests/test_config/config.yaml')
        print('config ===', config)

    def test_from_ini(self):
        config = GRPCFrameworkConfig.from_file('tests/test_config/config.ini')
        print('config ===', config)

    def test_from_json(self):
        config = GRPCFrameworkConfig.from_file('tests/test_config/config.json')
        print('config ===', config)
