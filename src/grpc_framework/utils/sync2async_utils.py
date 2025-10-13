import asyncio
from concurrent.futures import Executor
from typing import Optional, Callable


class Sync2AsyncUtils:
    def __init__(
            self,
            executor: Optional[Executor] = None
    ):
        self.executor = executor
        self.loop = asyncio.get_event_loop()

    async def run_function(self, func: Callable, *args):
        return await self.loop.run_in_executor(self.executor, func, *args)

    async def run_generate(self, gene: Callable, *args):
        async for item in self.loop.run_in_executor(self.executor, gene, *args):
            yield item
