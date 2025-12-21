import asyncio
import contextvars
from functools import partial
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
        """run a bio function in event loop with context propagation"""
        ctx = contextvars.copy_context()
        func_with_context = partial(ctx.run, func, *args)
        return await self.loop.run_in_executor(self.executor, func_with_context)

    async def run_generate(self, gene: Callable, *args):
        """run a bio generator in event loop with context propagation
        warning: its will the performance overhead is very high if generate so many item
        """
        ctx = contextvars.copy_context()
        
        def gene_with_context():
            return ctx.run(gene, *args)
            
        sync_iter = await self.loop.run_in_executor(self.executor, gene_with_context)
        
        while True:
            try:
                # We also need to run `next` in context, although usually the generator
                # state retains the context, but run_in_executor switches threads.
                # However, ctx.run(gene) executes the generator function which RETURNS a generator object.
                # The code inside the generator (up to yield) runs inside ctx.run.
                # BUT, subsequent `next(sync_iter)` calls will execute the code AFTER the yield.
                # If we just call `next(sync_iter)` in the executor, it runs in a bare thread.
                # We must wrap `next` with the SAME context to ensure continuity.
                
                next_with_context = partial(ctx.run, next, sync_iter)
                item = await self.loop.run_in_executor(self.executor, next_with_context)
                yield item
            except (StopIteration, RuntimeError):
                break
