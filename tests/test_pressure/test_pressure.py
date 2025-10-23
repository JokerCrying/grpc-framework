import time
import asyncio
import unittest
from src.grpc_framework.client import GRPCChannelPoolOptions, GRPCChannelPool, GRPCClient


class TestPressure(unittest.TestCase):
    def setUp(self):
        channel_pool = GRPCChannelPool(GRPCChannelPoolOptions(
            pool_mode='async'
        ))
        self.client = GRPCClient(
            channel_pool_manager=channel_pool,
            host='10.25.19.162',
            port=50051,
            request_serializer=lambda x: x,
            response_deserializer=lambda x: x
        )

    def test_unary_pressure(self):
        async def request():
            response = await self.client.unary_unary(
                full_name='/demo.UserService/create_user',
                request_data=b'{"name":"Jack"}'
            )
            return response

        async def run():
            start_time = time.time()
            tasks = [request() for _ in range(10000)]
            responses = await asyncio.gather(*tasks)
            # print(responses)
            print('use time ->', time.time() - start_time, 's')

        asyncio.run(run())
