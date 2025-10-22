import grpc.aio as grpc_aio
import json
import random
import string


async def create_channel_and_call():
    fullname = '/demo.GRPCFrameWorkDemoService/app_uu_func'
    channel = grpc_aio.insecure_channel(
        target='localhost:50051'
    )
    callfunc = channel.unary_unary(fullname, request_serializer=lambda x: x, response_deserializer=lambda x: x)
    resp = await callfunc(b'{}')
    print(resp)


async def call_stream():
    fullname = '/demo.GRPCFrameWorkDemoService/app_us_func'
    channel = grpc_aio.insecure_channel(
        target='localhost:50051'
    )
    callfunc = channel.unary_stream(fullname, request_serializer=lambda x: x, response_deserializer=lambda x: x)
    async for resp in callfunc(None):
        print(resp)


async def call_user_create():
    fullname = '/demo.UserService/create_user'
    channel = grpc_aio.insecure_channel(
        target='localhost:50051'
    )
    callfunc = channel.unary_unary(fullname, request_serializer=lambda x: x, response_deserializer=lambda x: x)
    resp = await callfunc(b'{"name":"Jack"}')
    print(resp)


async def call_iter_user():
    fullname = '/demo.UserService/iter_user'
    channel = grpc_aio.insecure_channel(
        target='localhost:50051'
    )
    callfunc = channel.unary_stream(fullname, request_serializer=lambda x: x, response_deserializer=lambda x: x)
    async for resp in callfunc(None):
        print(resp)


async def call_profile():
    fullname = '/demo.ProfileService/get_profile'
    channel = grpc_aio.insecure_channel(
        target='localhost:50051'
    )
    callfunc = channel.unary_unary(fullname, request_serializer=lambda x: x, response_deserializer=lambda x: x)
    resp = await callfunc(None)
    print(resp)


async def call_iter_profile():
    fullname = '/demo.ProfileService/iter_profile_counter'
    channel = grpc_aio.insecure_channel(
        target='localhost:50051'
    )
    callfunc = channel.unary_stream(fullname, request_serializer=lambda x: x, response_deserializer=lambda x: x)
    async for resp in callfunc(b'{"counter":10}'):
        print(resp)


async def call_sum_counter():
    async def iterable():
        for i in range(1, 10):
            data = json.dumps({'counter': i})
            yield data.encode('utf-8')

    fullname = '/demo.ProfileService/sum_counter'
    channel = grpc_aio.insecure_channel(
        target='localhost:50051'
    )
    callfunc = channel.stream_unary(fullname, request_serializer=lambda x: x, response_deserializer=lambda x: x)
    resp = await callfunc(iterable())
    print(resp)


async def call_chat():
    async def chat_iter():
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
    fullname = '/demo.ProfileService/simulated_chat'
    channel = grpc_aio.insecure_channel(
        target='localhost:50051'
    )
    callfunc = channel.stream_stream(fullname, request_serializer=lambda x: x, response_deserializer=lambda x: x)
    async for resp in callfunc(chat_iter()):
        print(resp)


if __name__ == '__main__':
    import asyncio

    asyncio.run(create_channel_and_call())
    print('=' * 30)
    asyncio.run(call_stream())
    print('=' * 30)
    asyncio.run(call_user_create())
    print('=' * 30)
    asyncio.run(call_iter_user())
    print('=' * 30)
    asyncio.run(call_profile())
    print('=' * 30)
    asyncio.run(call_iter_profile())
    print('=' * 30)
    asyncio.run(call_sum_counter())
    print('=' * 30)
    asyncio.run(call_chat())
