import asyncio
import unittest
import grpc
from typing import AsyncIterator
from src.grpc_framework import GRPCFramework, GRPCFrameworkConfig, Service, unary_unary, unary_stream
from src.grpc_framework.core.di.depends import Depends
from src.grpc_framework.utils.sync2async_utils import Sync2AsyncUtils
from concurrent.futures import ThreadPoolExecutor


# --- Dependencies ---
async def get_db():
    yield "db_connection"

def get_config():
    return {"debug": True}

async def get_service(
    db: str = Depends(get_db),
    config: dict = Depends(get_config)
):
    return f"Service(db={db}, debug={config['debug']})"


# --- CBV Service ---
class UserService(Service):
    def __init__(self):
        super().__init__()

    @unary_unary
    async def get_user(
        self, 
        user_id: int, 
        service: str = Depends(get_service)
    ):
        return {"id": user_id, "service": service}

    @unary_stream
    async def stream_users(
        self, 
        prefix: str,
        db: str = Depends(get_db)
    ):
        yield {"name": f"{prefix}_1", "source": db}
        yield {"name": f"{prefix}_2", "source": db}


# --- FBV Handlers ---
async def health_check(
    db: str = Depends(get_db)
):
    return {"status": "ok", "db": db}

async def complex_op(
    service: str = Depends(get_service)
):
    return {"result": service}


# --- Test App Setup ---
class TestAppIntegration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.config = GRPCFrameworkConfig(
            port=50052,  # Use a different port to avoid conflict
            app_service_name="TestService",
            package='test'
        )
        self.app = GRPCFramework(self.config)
        
        # Register FBV
        self.app.unary_unary(health_check)
        self.app.unary_unary(complex_op)
        
        # Register CBV
        self.app.add_service(UserService)
        
        # Note: We are testing the integration logic, primarily parameter resolution.
        # Since we cannot easily start a full gRPC server and client in a unit test 
        # without complex setup (protoc compilation, etc.), we will test the 
        # internal logic that the framework uses to resolve dependencies.
        # Specifically, we will verify that the GRPCAdaptor correctly resolves
        # dependencies for these registered endpoints.

    async def test_dependency_resolution_fbv(self):
        """Test dependency resolution for FBV endpoints."""
        # Manually create a scope and resolve dependencies for the handler
        # This simulates what GRPCAdaptor does internally
        
        async with self.app.dependency_scope() as scope:
            # Test health_check resolution
            # health_check has 'db' dependency
            # We use the internal provider logic to verify it works
            
            # 1. Resolve 'get_db'
            db = await scope.resolve(Depends(get_db))
            self.assertEqual(db, "db_connection")
            
            # 2. Resolve 'get_service' (nested)
            svc = await scope.resolve(Depends(get_service))
            self.assertEqual(svc, "Service(db=db_connection, debug=True)")

    async def test_fbv_call_logic(self):
        """Simulate FBV call with dependencies."""
        # We can't easily call app.dispatch without a real gRPC context,
        # but we can test the dependency injection logic in isolation.
        
        async with self.app.dependency_scope() as scope:
            # Simulate calling health_check
            # Arguments from request would be empty for this test
            kwargs = {
                "db": await scope.resolve(Depends(get_db))
            }
            result = await health_check(**kwargs)
            self.assertEqual(result, {"status": "ok", "db": "db_connection"})
            
            # Simulate calling complex_op
            kwargs = {
                "service": await scope.resolve(Depends(get_service))
            }
            result = await complex_op(**kwargs)
            self.assertEqual(result["result"], "Service(db=db_connection, debug=True)")

    async def test_cbv_call_logic(self):
        """Simulate CBV call with dependencies."""
        service = UserService()
        
        async with self.app.dependency_scope() as scope:
            # Simulate get_user call
            kwargs = {
                "user_id": 123,
                "service": await scope.resolve(Depends(get_service))
            }
            result = await service.get_user(**kwargs)
            self.assertEqual(result["id"], 123)
            self.assertEqual(result["service"], "Service(db=db_connection, debug=True)")
            
            # Simulate stream_users call
            kwargs = {
                "prefix": "test",
                "db": await scope.resolve(Depends(get_db))
            }
            results = []
            async for item in service.stream_users(**kwargs):
                results.append(item)
            
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["source"], "db_connection")


if __name__ == '__main__':
    unittest.main()
