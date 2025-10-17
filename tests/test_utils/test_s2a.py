import time
import asyncio
import unittest
from src.grpc_framework.utils import Sync2AsyncUtils


class TestSync2Async(unittest.TestCase):
    @staticmethod
    def run_func():
        print('func start')
        time.sleep(1)
        print('func end')

    @staticmethod
    def run_gene():
        for i in range(1, 10):
            yield i
            time.sleep(0.5)

    def test(self):
        s2a = Sync2AsyncUtils()
        rfa = s2a.run_function(self.run_func)
        loop = asyncio.get_event_loop()

        async def run_rfg():
            rfg = s2a.run_generate(self.run_gene)
            async for i in rfg:
                print(i)

        async def run_rfg_mul():
            tasks = [run_rfg() for _ in range(10)]
            await asyncio.gather(*tasks)

        loop.run_until_complete(run_rfg())
        print('-' * 30)
        loop.run_until_complete(rfa)
        print('-' * 30)
        loop.run_until_complete(run_rfg_mul())
