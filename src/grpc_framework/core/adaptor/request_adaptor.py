from ...core.enums import Interaction
from typing import Any, TYPE_CHECKING, Optional, Dict
from ..request.request import Request
from .domain import StreamRequest
from ...types import T
from ..params import ParamInfo
from ...exceptions import GRPCException

if TYPE_CHECKING:
    from ...application import GRPCFramework


class RequestAdaptor:
    def __init__(self,
                 interaction_type: Interaction,
                 app: 'GRPCFramework',
                 input_param_info: Dict[str, ParamInfo],
                 request: Request):
        self.interaction_type = interaction_type
        self.request_bytes = request.request_bytes
        self.app = app
        self.input_param_info = input_param_info
        self.request = request

    def unary_request(self, key: str):
        return self.deserialize_request(self.request_bytes, self.input_param_info[key])

    def stream_request(self, key: str) -> StreamRequest[T]:
        return StreamRequest(self.request, self.deserialize_request, self.input_param_info[key])

    def deserialize_request(self, request_bytes: Any, model_type: ParamInfo) -> Any:
        """Deserialize the original request data into a domain model"""
        if self.request.is_request_bytes_empty():
            raise ValueError("Request bytes not set. Call adapt_request first.")
        if model_type.union_types or model_type.generic_args:
            model_list = [
                *(model_type.union_types or []),
                *(model_type.generic_args or [])
            ]
            errors = []
            for mt in model_list:
                try:
                    return self.app.load_content(request_bytes, mt)
                except Exception as e:
                    errors.append(e)
                    continue
            return self.request_bytes
        else:
            return self.app.load_content(request_bytes, model_type.type)

    def request_model(self, key: str):
        if self.interaction_type is Interaction.unary:
            return self.unary_request(key)
        return self.stream_request(key)
