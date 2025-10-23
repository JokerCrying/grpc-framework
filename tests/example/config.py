from src.grpc_framework import DataclassesCodec, DataclassesConverter

package = 'demo'

name = 'grpc-framework-demo'

version = '1.0.0.beta'

host = '[::]'

port = 50051

reflection = True

add_health_check = True

app_service_name = 'GRPCFrameWorkDemoService'

codec = DataclassesCodec

converter = DataclassesConverter

grpc_options = [
    ('grpc.max_concurrent_streams', 30000),
    ('grpc.so_reuseport', 1),
    ('grpc.http2.max_frame_size', 8 * 1024 * 1024),
    ('grpc.http2.enable_zerocopy', 1)
]
