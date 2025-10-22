import grpc
from grpc.aio import ServicerContext
from contextvars import ContextVar
from typing import Type, TYPE_CHECKING, Union, Optional, Any
from dataclasses import dataclass
from ...types import StrAnyDict, BytesLike, StrDict

if TYPE_CHECKING:
    from ..service import RPCFunctionMetadata


# Default Request Context Var
class _EmptyRequest: ...


# Default Request Bytes
class _EmptyRequestBytes: ...


REQUEST_CONTEXT_VAR_TYPE = ContextVar[Union['Request', Type[_EmptyRequest]]]
_current_request: REQUEST_CONTEXT_VAR_TYPE = ContextVar('current_request', default=_EmptyRequest)


@dataclass
class PeerInfo:
    """Store parsed peer information

    Args:
        ip_version: ipv4/ipv5
        ip: ip address
        port: port
        raw: original data, .temp: ip_version:ip:port
    """
    ip_version: Optional[str] = None
    ip: Optional[str] = None
    port: Optional[int] = None
    raw: Optional[str] = None


class Request:
    """gRPC Request Instance

    Args:
        peer_info_dict: a dict for build PeerInfo instance, it represents the network information in this request
        full_method: request address, .temp: /package.service/method
        metadata: a dict represents request metadata in this request
        compression: grpc.Compression
        grpc_context: grpc's context in this request
    """

    def __init__(
            self,
            peer_info_dict: Optional[StrAnyDict] = None,
            full_method: Optional[str] = None,
            metadata: Optional[StrAnyDict] = None,
            compression: Optional[grpc.Compression] = None,
            grpc_context: Optional[ServicerContext] = None
    ):
        self.peer_info: Optional[PeerInfo] = peer_info_dict
        self.metadata: StrAnyDict = metadata or {}
        self.package: Optional[str] = None
        self.service_name: Optional[str] = None
        self.method_name: Optional[str] = None
        self.full_method: Optional[str] = full_method
        self.compression: Optional[str] = compression
        self.grpc_context: Optional[ServicerContext] = grpc_context
        self.state: StrAnyDict = {}
        self.request_bytes: Any = _EmptyRequestBytes
        self.current_request_metadata: Optional['RPCFunctionMetadata'] = None
        # set current request
        _current_request.set(self)

    def from_handler_details(self, handler_details):
        # its just first step to parse full request instance
        # methods parse
        self.full_method = handler_details.method
        self._parse_pkg_svc_method()
        # metadata parse
        metadata = {
            i.key: i.value for i in
            handler_details.invocation_metadata
        }
        self.metadata = metadata

    def from_context(self, context):
        # parse peer || network information
        peer_raw = context.peer()
        self._parse_peer(peer_raw)

    def set_request_bytes(self, request_bytes: BytesLike):
        self.request_bytes = request_bytes

    @classmethod
    def current(cls) -> 'Request':
        request = _current_request.get()
        if request is _EmptyRequest:
            raise RuntimeError(
                "Request.current() be invoked, However, there is no Request instance in the current context，"
                "Please ensure that you use it in the gRPC request processing flow."
            )
        return request

    def _parse_pkg_svc_method(self):
        if not self.full_method:
            return
        pkg_svc, method = self.full_method.strip('/').split('/')
        pkg_svc_split = pkg_svc.split('.')
        if len(pkg_svc_split) == 1:
            self.service_name = pkg_svc_split[0]
        else:
            pkg, svc = pkg_svc_split[:2]
            self.package = pkg
            self.service_name = svc
        self.method_name = method

    def _parse_peer(self, raw: str):
        if not raw:
            self.peer_info = PeerInfo()
        try:
            ip_version, rest = raw.split(':', 1)
            if ':' in rest:
                ip, port = rest.rsplit(':', 1)
                self.peer_info = PeerInfo(ip_version=ip_version, ip=ip, port=int(port), raw=raw)
            else:
                self.peer_info = PeerInfo(ip_version=ip_version, raw=raw)
        except Exception:
            self.peer_info = PeerInfo(raw=raw)

    def send_metadata(self, key: str, value: Union[str, BytesLike]):
        """call grpc context send initial metadata"""
        self.grpc_context.send_initial_metadata((key, value))

    def abort(self, code: grpc.StatusCode, detail: str, metadata: Optional[StrDict] = None):
        """call grpc context abort"""
        self.grpc_context.abort(code, detail, metadata or {})

    def is_request_bytes_empty(self) -> bool:
        """is current request bytes empty"""
        return self.request_bytes is _EmptyRequestBytes

    def __repr__(self):
        return (
            f"<Request peer={self.peer_info.ip}:{self.peer_info.port} "
            f"service={self.service_name} method={self.method_name} "
            f"metadata={self.metadata}>"
        )
