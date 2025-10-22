import grpc
from typing import Any, Union, TYPE_CHECKING, Callable
from ...types import StrDict, BytesLike
from ..request.request import Request

if TYPE_CHECKING:
    from ...application import GRPCFramework


class Response:
    def __init__(
            self,
            content: Any,
            app: 'GRPCFramework',
            status_code: grpc.StatusCode = grpc.StatusCode.OK,
            metadata: StrDict = None,
    ):
        self._request = Request.current()
        self.app = app
        self.content = content
        self.status_code = status_code
        self.metadata = metadata or {}
        self.package = self._request.package
        self.service_name = self._request.service_name
        self.method_name = self._request.method_name

    def _set_grpc_metadata(self):
        """call grpc context set trailing metadata"""
        if not self.metadata:
            return
        for key, value in self.metadata.items():
            self._request.grpc_context.set_trailing_metadata((key, value))

    def set_metadata(self, key: str, value: Union[str, BytesLike]):
        """set a memory metadata"""
        self.metadata[key] = value

    def abort(self, code: grpc.StatusCode, detail: str):
        """call grpc context abort"""
        self._request.grpc_context.abort(code, detail, self.metadata)

    def render(self):
        self._set_grpc_metadata()
        if self.content is None:
            return b''
        elif isinstance(self.content, BytesLike):
            return self.content
        else:
            return self.serialize_response(self.content)

    def serialize_response(self, response_model: Any) -> bytes:
        """Serialize the domain model into response data"""
        return self.app.render_content(response_model)
