import asyncio
import time
import uuid
from grpc.aio import insecure_channel


async def call(index):
    # [关键] 生成一个随机的 channel argument
    # 这会欺骗 gRPC C-Core，让它认为这是一个全新的配置，从而强制建立新的 TCP 连接
    random_arg = f'unique_session_{uuid.uuid4()}'
    options = [('grpc.primary_user_agent', random_arg)]

    try:
        async with insecure_channel('localhost:50051', options=options) as channel:
            gene = channel.unary_unary('/demo.GRPCFrameWorkDemoService/app_uu_func')
            # 这里的 request 随便填
            result = await gene(request=b'{}')
            print(f"Request {index} finished.")
    except Exception as e:
        print(f"Request {index} error: {e}")


async def run_concurrent_test():
    tasks = []
    print("Starting 20 concurrent requests with FORCED new connections...")
    for i in range(20):
        tasks.append(call(i))

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    start = time.time()
    asyncio.run(run_concurrent_test())
    print(f"Total time: {time.time() - start:.4f}s")
