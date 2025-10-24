from src.grpc_framework import GRPCFramework, GRPCFrameworkConfig
import tests.test_native_app.e_pb2 as e_pb2
import asyncio
import random
import uuid

app = GRPCFramework(
    config=GRPCFrameworkConfig(
        package='native',
        host='[::]',
        app_service_name='NativeService',
        grpc_options=[
            ('grpc.max_concurrent_streams', 30000),
            ('grpc.so_reuseport', 1),
            ('grpc.http2.max_frame_size', 8 * 1024 * 1024),
            ('grpc.http2.enable_zerocopy', 1),
            ('grpc.optimization_target', 'latency')
        ]
    )
)


@app.unary_unary
async def run_native():
    await asyncio.sleep(0.1)
    return e_pb2.UserResponse(id=random.randint(1, 10), name=f'{uuid.uuid4()}')


if __name__ == '__main__':
    app.run()
