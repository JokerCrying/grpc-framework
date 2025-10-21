from src.grpc_framework.core.enums import Interaction
from typing import Any, TYPE_CHECKING, Optional
from ..request.request import Request
from .domain import StreamRequest
from ...types import T
from ..params import ParamInfo

if TYPE_CHECKING:
    from ...application import GRPCFramework


class RequestAdaptor:
    def __init__(self,
                 interaction_type: Interaction,
                 app: 'GRPCFramework',
                 input_param_info: ParamInfo,
                 request: Request):
        self.interaction_type = interaction_type
        self.request_bytes = request.request_bytes
        self.app = app
        self.input_param_info = input_param_info
        self.request = request

    def unary_request(self):
        return self.deserialize_request(self.request_bytes, self.input_param_info.type)

    def stream_request(self) -> StreamRequest[T]:
        return StreamRequest(self.request_bytes, self.deserialize_request, self.input_param_info.type)

    def deserialize_request(self, request: Request, model_type: type) -> Any:
        """Deserialize the original request data into a domain model"""
        if request.is_request_bytes_empty():
            raise ValueError("Request bytes not set. Call adapt_request first.")

        return self.app.load_content(request.request_bytes, model_type)

    def request_model(self):
        if self.interaction_type is Interaction.unary:
            return self.unary_request()
        return self.stream_request()
