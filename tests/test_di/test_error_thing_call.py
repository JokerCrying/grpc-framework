from src.grpc_framework.client import GRPCClient, GRPCChannelPoolOptions, GRPCChannelPool
import json

pool = GRPCChannelPool(
    GRPCChannelPoolOptions(
        'default'
    )
)

client = GRPCClient(
    pool,
    request_serializer=lambda x: json.dumps(x, ensure_ascii=False).encode('utf8'),
    response_deserializer=json.loads
)

resp = client.unary_unary(
    '/test.UserService/get_peer',
    request_data={}
)

print(resp)

