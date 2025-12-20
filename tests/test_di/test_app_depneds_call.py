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
    '/test.UserService/redis_test',
    request_data={}
)
print(resp)
