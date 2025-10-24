import time
import winloop
import asyncio
import unittest
import tests.example_grpc_proto.example_pb2_grpc as example_pb2_grpc
import tests.example_grpc_proto.example_pb2 as example_pb2
from src.grpc_framework.client import GRPCChannelPoolOptions, GRPCChannelPool, GRPCClient


class TestPressure(unittest.TestCase):
    def setUp(self):
        winloop.install()
        channel_pool = GRPCChannelPool(GRPCChannelPoolOptions(
            pool_mode='async'
        ))
        self.client = GRPCClient(
            channel_pool_manager=channel_pool,
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

    def test_stub_pressure(self):
        async def request():
            req = example_pb2.SimpleRequest(query='1', page_number=1, result_per_page=20)
            channel = self.client.channel_pool_manager.get()
            impl = example_pb2_grpc.SimpleServiceStub(channel)
            resp = await self.client.call_method(impl.GetSimpleResponse, req)
            return resp

        async def run():
            start_time = time.time()
            tasks = [request() for _ in range(100)]
            responses = await asyncio.gather(*tasks)
            # print(responses)
            print('use time ->', time.time() - start_time, 's')

        asyncio.run(run())

    def test_protobuf_codec(self):
        async def request():
            response = await self.client.unary_unary(
                full_name='/native.NativeService/run_native',
                request_data=None
            )
            return response

        async def run():
            start_time = time.time()
            tasks = [request() for _ in range(100)]
            responses = await asyncio.gather(*tasks)
            # print(responses)
            print('use time ->', time.time() - start_time, 's')


        asyncio.run(run())
