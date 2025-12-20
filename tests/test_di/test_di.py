import unittest
import asyncio
from src.grpc_framework.core.di.container import DependencyContainer, DependencyScope
from src.grpc_framework.core.di.depends import Depends
from src.grpc_framework.utils.sync2async_utils import Sync2AsyncUtils


# Mock Sync2AsyncUtils
class MockSync2AsyncUtils(Sync2AsyncUtils):
    def __init__(self):
        super().__init__()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
    async def run_function(self, func, *args):
        if asyncio.iscoroutinefunction(func):
            return await func(*args)
        return func(*args)


class TestDI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.container = DependencyContainer()
        self.s2a = MockSync2AsyncUtils()
        self.scope = self.container.scope(self.s2a)

    async def asyncSetUp(self):
        pass

    async def asyncTearDown(self):
        await self.scope.__aexit__(None, None, None)
        if hasattr(self.s2a.loop, "close"):
             if not self.s2a.loop.is_closed():
                 self.s2a.loop.close()

    async def test_simple_dependency(self):
        """Test simple async function dependency."""
        async def dep():
            return "value"
        
        result = await self.scope.resolve(Depends(dep))
        self.assertEqual(result, "value")

    async def test_nested_dependency(self):
        """Test dependency depending on another dependency."""
        async def dep1():
            return "dep1"
        
        async def dep2(d1: str = Depends(dep1)):
            return f"dep2-{d1}"
        
        result = await self.scope.resolve(Depends(dep2))
        self.assertEqual(result, "dep2-dep1")

    async def test_singleton_in_scope(self):
        """Test that dependencies are singletons within a scope."""
        count = 0
        async def counter():
            nonlocal count
            count += 1
            return count
        
        # Resolve twice
        val1 = await self.scope.resolve(Depends(counter))
        val2 = await self.scope.resolve(Depends(counter))
        
        self.assertEqual(val1, 1)
        self.assertEqual(val2, 1)  # Should return cached value
        self.assertEqual(count, 1)

    async def test_sync_generator_dependency(self):
        """Test sync generator dependency with setup and teardown."""
        events = []
        
        def sync_gen_dep():
            events.append("setup")
            yield "resource"
            events.append("teardown")
        
        # We need to manually manage scope context for generator cleanup test
        # because setUp creates a scope that isn't entered via 'async with'
        # but we can simulate it or use a new scope
        
        async with self.container.scope(self.s2a) as scope:
            result = await scope.resolve(Depends(sync_gen_dep))
            self.assertEqual(result, "resource")
            self.assertEqual(events, ["setup"])
        
        self.assertEqual(events, ["setup", "teardown"])

    async def test_async_generator_dependency(self):
        """Test async generator dependency with setup and teardown."""
        events = []
        
        async def async_gen_dep():
            events.append("setup")
            yield "resource"
            events.append("teardown")
        
        async with self.container.scope(self.s2a) as scope:
            result = await scope.resolve(Depends(async_gen_dep))
            self.assertEqual(result, "resource")
            self.assertEqual(events, ["setup"])
        
        self.assertEqual(events, ["setup", "teardown"])

    async def test_dependency_registration(self):
        """Test registering dependencies via container."""
        class Config:
            pass
            
        config_instance = Config()
        
        # Register factory for Config type
        self.container.register(Config, lambda: config_instance)
        
        result = await self.scope.resolve(Config)
        self.assertIs(result, config_instance)

    async def test_mixed_sync_async_dependencies(self):
        """Test mixing sync and async dependencies."""
        def sync_dep():
            return "sync"
            
        async def async_dep(s: str = Depends(sync_dep)):
            print('s =', s)
            return f"async-{s}"
            
        result = await self.scope.resolve(Depends(async_dep))
        self.assertEqual(result, "async-sync")

if __name__ == '__main__':
    unittest.main()
