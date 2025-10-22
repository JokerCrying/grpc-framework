import unittest
from src.grpc_framework.client import GRPCChannelPool


class TestChannelPool(unittest.TestCase):
    def test_default_mode(self):
        channel_pool = GRPCChannelPool({
            'min_size': 10,
            'max_size': 10,
            'host': 'localhost',
            'port': 50051,
            'secure_mode': False,
            'credit': None,
            'maintenance_interval': 5,
            'auto_preheating': True,
            'channel_options': {},
            'pool_mode': 'default'
        })
        print(channel_pool.get())

    def test_async_mode(self):
        channel_pool = GRPCChannelPool({
            'min_size': 10,
            'max_size': 10,
            'host': 'localhost',
            'port': 50051,
            'secure_mode': False,
            'credit': None,
            'maintenance_interval': 5,
            'auto_preheating': True,
            'channel_options': {},
            'pool_mode': 'async'
        })
        print(channel_pool.get())
