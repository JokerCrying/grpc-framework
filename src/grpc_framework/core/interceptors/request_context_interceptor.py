import grpc
import grpc.aio as grpc_aio
from typing import TYPE_CHECKING, Callable, Awaitable
from ..request.request import Request

if TYPE_CHECKING:
    from ...application import GRPCFramework


class RequestContextInterceptor(grpc_aio.ServerInterceptor):
    def __init__(self, app: 'GRPCFramework'):
        self.app = app

    async def intercept_service(self, continuation: Callable[
        [grpc.HandlerCallDetails], Awaitable[grpc.RpcMethodHandler]
    ], handler_call_details: grpc.HandlerCallDetails):
        # 初步解析Request
        request = Request()
        request.from_handler_details(handler_call_details)
        
        # 获取原始handler
        original_handler = await continuation(handler_call_details)
        
        if original_handler is None:
            return None
        
        # 查找对应的endpoint元数据
        try:
            endpoint_meta = self.app.find_endpoint(
                request.package or '', 
                request.service_name or '', 
                request.method_name or ''
            )
            
            # 使用适配器包装handler
            from ..adaptor import GRPCAdaptor
            adaptor = GRPCAdaptor(self.app)
            
            # 这里需要根据实际情况获取请求和响应的模型类型
            # 可以从handler的类型注解或者配置中获取
            request_model_type = self._get_request_model_type(endpoint_meta)
            response_model_type = self._get_response_model_type(endpoint_meta)
            
            wrapped_handler = await adaptor.wrap_handler_by_interaction(
                endpoint_meta['handler'],
                endpoint_meta['request_interaction'],
                endpoint_meta['response_interaction'],
                request_model_type,
                response_model_type
            )
            
            # 替换原始handler
            if hasattr(original_handler, 'unary_unary'):
                original_handler.unary_unary = wrapped_handler
            elif hasattr(original_handler, 'unary_stream'):
                original_handler.unary_stream = wrapped_handler
            elif hasattr(original_handler, 'stream_unary'):
                original_handler.stream_unary = wrapped_handler
            elif hasattr(original_handler, 'stream_stream'):
                original_handler.stream_stream = wrapped_handler
                
        except Exception as e:
            # 如果找不到endpoint或包装失败，返回原始handler
            print(f"Failed to wrap handler: {e}")
        
        return original_handler
    
    def _get_request_model_type(self, endpoint_meta):
        """从endpoint元数据中获取请求模型类型"""
        # 这里可以通过类型注解、配置或约定来获取
        # 示例实现，实际需要根据你的设计调整
        handler = endpoint_meta['handler']
        if hasattr(handler, '__annotations__'):
            annotations = handler.__annotations__
            # 假设第一个参数是请求模型
            params = list(annotations.keys())
            if len(params) > 0 and params[0] != 'return':
                return annotations[params[0]]
        return bytes  # 默认返回bytes类型
    
    def _get_response_model_type(self, endpoint_meta):
        """从endpoint元数据中获取响应模型类型"""
        handler = endpoint_meta['handler']
        if hasattr(handler, '__annotations__'):
            return handler.__annotations__.get('return', bytes)
        return bytes  # 默认返回bytes类型
