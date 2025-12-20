import json
from src.grpc_framework.client import GRPCChannelPool, GRPCChannelPoolOptions, GRPCClient


pool = GRPCChannelPool(
    GRPCChannelPoolOptions(
        pool_mode='default'
    )
)
client = GRPCClient(
    pool,
    request_serializer=lambda x: json.dumps(x, ensure_ascii=False).encode('utf-8'),
    response_deserializer=json.loads
)


resp = client.unary_unary(
    '/test.RootService/health_check',
    request_data={}
)
print(resp)

resp = client.unary_unary(
    '/test.RootService/complex_op',
    request_data={}
)
print(resp)

resp = client.unary_unary(
    '/test.RootService/redis',
    request_data={}
)
print(resp)

resp = client.unary_unary(
    '/test.UserService/redis_test',
    request_data={}
)
print(resp)

resp = client.unary_unary(
    '/test.UserService/redis_test2',
    request_data={}
)
print(resp)

resp = client.unary_unary(
    '/test.UserService/get_user',
    request_data={}
)
print(resp)


for resp in client.unary_stream(
    '/test.UserService/stream_users',
    request_data={}
):
    print(resp)
