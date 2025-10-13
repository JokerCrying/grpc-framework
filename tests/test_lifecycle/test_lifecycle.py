import asyncio
import unittest
from src.grpc_framework.application import GRPCFramework

app = GRPCFramework()


@app.lifecycle
def lifespan(_):
    print('- DB in initialization')
    print('- DB init success')
    yield
    print('- DB closed')
    print('-', _, 'stop')


class TestLifecycle(unittest.TestCase):
    def test_lifecycle(self):
        async def run_lifecycle():
            async with app._lifecycle_manager.context(app):
                print('- Server running now.')
                await asyncio.sleep(3)
        asyncio.run(run_lifecycle())
