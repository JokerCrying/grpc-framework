import inspect
from typing import Optional, Sequence, TYPE_CHECKING, Any, Callable
from ..utils import Sync2AsyncUtils
from .request.request import Request
from .response.response import Response
from .enums import Interaction

if TYPE_CHECKING:
    from ..application import GRPCFramework


class GRPCAdaptor:
    def __init__(self, app: 'GRPCFramework'):
        self.app = app
        self.s2a = Sync2AsyncUtils(self.app.config.executor)

    @staticmethod
    async def adapt_request(request: Request, request_data: bytes, context) -> Request:
        """二次解析Request：补充原始请求数据和上下文信息"""
        # 设置原始请求数据
        request.set_request_bytes(request_data)
        # 从grpc context补充网络信息
        request.from_context(context)
        # 设置grpc上下文
        request.grpc_context = context
        return request

    async def deserialize_request(self, request: Request, model_type: type) -> Any:
        """将原始请求数据反序列化为域模型"""
        if not hasattr(request, 'request_bytes') or request.request_bytes is None:
            raise ValueError("Request bytes not set. Call adapt_request first.")
        
        return self.app._serializer.deserialize(request.request_bytes, model_type)

    async def serialize_response(self, response_model: Any) -> bytes:
        """将域模型序列化为响应数据"""
        return self.app._serializer.serialize(response_model)

    async def call_handler(self, handler: Callable, request_model: Any, request: Request) -> Any:
        """调用业务handler"""
        if inspect.iscoroutinefunction(handler):
            return await handler(request_model, request)
        else:
            return await self.s2a.run_function(handler, request_model, request)

    async def wrap_unary_unary_handler(self, handler: Callable, request_model_type: type, response_model_type: type):
        """包装unary-unary类型的handler"""
        async def wrapper(request_data: bytes, context):
            # 获取当前请求实例
            request = Request.current()
            
            # 二次解析Request
            request = await self.adapt_request(request, request_data, context)
            
            # 通过中间件链路处理
            async def handler_wrapper(req: Request):
                # 反序列化请求数据为域模型
                request_model = await self.deserialize_request(req, request_model_type)
                
                # 进入请求上下文管理器
                async with self.app.start_request_context(req) as ctx:
                    # 调用业务handler
                    response_model = await self.call_handler(handler, request_model, req)
                    
                    # 序列化响应
                    response_data = await self.serialize_response(response_model)
                    
                    return response_data
            
            # 通过中间件链路处理请求
            return await self.app._middleware_manager.dispatch(request, handler_wrapper)
        
        return wrapper

    async def wrap_unary_stream_handler(self, handler: Callable, request_model_type: type, response_model_type: type):
        """包装unary-stream类型的handler"""
        async def wrapper(request_data: bytes, context):
            request = Request.current()
            request = await self.adapt_request(request, request_data, context)
            
            async def handler_wrapper(req: Request):
                request_model = await self.deserialize_request(req, request_model_type)
                
                async with self.app.start_request_context(req) as ctx:
                    # handler返回异步生成器
                    async for response_model in self.call_handler(handler, request_model, req):
                        response_data = await self.serialize_response(response_model)
                        yield response_data
            
            async for response in self.app._middleware_manager.dispatch(request, handler_wrapper):
                yield response
        
        return wrapper

    async def wrap_stream_unary_handler(self, handler: Callable, request_model_type: type, response_model_type: type):
        """包装stream-unary类型的handler"""
        async def wrapper(request_iterator, context):
            request = Request.current()
            # 对于stream请求，先用空数据初始化
            request = await self.adapt_request(request, b'', context)
            
            async def handler_wrapper(req: Request):
                # 反序列化请求流
                async def request_model_iterator():
                    async for request_data in request_iterator:
                        yield await self.deserialize_request_data(request_data, request_model_type)
                
                async with self.app.start_request_context(req) as ctx:
                    response_model = await self.call_handler(handler, request_model_iterator(), req)
                    return await self.serialize_response(response_model)
            
            return await self.app._middleware_manager.dispatch(request, handler_wrapper)
        
        return wrapper

    async def wrap_stream_stream_handler(self, handler: Callable, request_model_type: type, response_model_type: type):
        """包装stream-stream类型的handler"""
        async def wrapper(request_iterator, context):
            request = Request.current()
            request = await self.adapt_request(request, b'', context)
            
            async def handler_wrapper(req: Request):
                async def request_model_iterator():
                    async for request_data in request_iterator:
                        yield await self.deserialize_request_data(request_data, request_model_type)
                
                async with self.app.start_request_context(req) as ctx:
                    async for response_model in self.call_handler(handler, request_model_iterator(), req):
                        response_data = await self.serialize_response(response_model)
                        yield response_data
            
            async for response in self.app._middleware_manager.dispatch(request, handler_wrapper):
                yield response
        
        return wrapper

    async def deserialize_request_data(self, request_data: bytes, model_type: type) -> Any:
        """直接反序列化请求数据（用于流式处理）"""
        return self.app._serializer.deserialize(request_data, model_type)

    def wrap_handler_by_interaction(self, handler: Callable, request_interaction, response_interaction, 
                                   request_model_type: type, response_model_type: type):
        """根据交互类型选择合适的包装器"""
        if request_interaction == Interaction.unary and response_interaction == Interaction.unary:
            return self.wrap_unary_unary_handler(handler, request_model_type, response_model_type)
        elif request_interaction == Interaction.unary and response_interaction == Interaction.stream:
            return self.wrap_unary_stream_handler(handler, request_model_type, response_model_type)
        elif request_interaction == Interaction.stream and response_interaction == Interaction.unary:
            return self.wrap_stream_unary_handler(handler, request_model_type, response_model_type)
        elif request_interaction == Interaction.stream and response_interaction == Interaction.stream:
            return self.wrap_stream_stream_handler(handler, request_model_type, response_model_type)
        else:
            raise ValueError(f"Unsupported interaction types: {request_interaction}, {response_interaction}")
