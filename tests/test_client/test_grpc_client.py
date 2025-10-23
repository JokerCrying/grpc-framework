import json
import random
import string
import asyncio
import unittest
from src.grpc_framework.client import GRPCChannelPool, GRPCClient


class UserResults(unittest.TestCase):
    def setUp(self):
        channel_pool = GRPCChannelPool({
            'min_size': 5,
            'max_size': 10,
            'secure_mode': False,
            'credit': None,
            'maintenance_interval': 10,
            'auto_preheating': True,
            'channel_options': {},
            'pool_mode': 'async'
        })
        self.client = GRPCClient(
            channel_pool_manager=channel_pool,
            request_serializer=lambda x: x,
            response_deserializer=lambda x: x
        )

    def test_unary_api(self):
        async def run():
            response = await self.client.unary_unary(
                full_name='/demo.UserService/create_user',
                request_data=b'{"name":"Jack"}'
            )
            print(response)

        asyncio.run(run())
        print('call unary success'.center(100, '*'))

    def test_unary_stream_api(self):
        async def run():
            async for response in self.client.unary_stream(
                    full_name='/demo.ProfileService/iter_profile_counter',
                    request_data=b'{"counter": 10}'
            ):
                print(response)

        asyncio.run(run())
        print('call unary stream success'.center(100, '*'))

    def test_stream_unary_api(self):
        async def run():
            async def iter_request():
                for i in range(10, 21):
                    data = json.dumps({'counter': i})
                    yield data.encode('utf-8')

            response = await self.client.stream_unary(
                full_name='/demo.ProfileService/sum_counter',
                request_data=iter_request()
            )
            print(response)

        asyncio.run(run())
        print('call stream unary success'.center(100, '*'))

    def test_stream_stream_api(self):
        async def run():
            async def iter_request():
                for _ in range(random.randint(10, 20)):
                    chat_data = {
                        'user_id': random.randint(1, 9999),
                        'to_user_id': random.randint(1, 9999),
                        'message': ''.join(random.choices(string.ascii_letters, k=random.randint(3, 10))),
                        'message_type': random.choice(['img', 'video', 'text', 'voice'])
                    }
                    if chat_data['message_type'] not in ['text']:
                        chat_data['message'] = f'https://example.com/{chat_data["message"]}'
                    data = json.dumps(chat_data)
                    yield data.encode('utf-8')

            async for response in self.client.stream_stream(
                    full_name='/demo.ProfileService/simulated_chat',
                    request_data=iter_request()
            ):
                print(response)

        asyncio.run(run())
        print('call stream success'.center(100, '*'))
