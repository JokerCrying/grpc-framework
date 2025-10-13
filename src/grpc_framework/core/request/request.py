import re
from grpc.aio import ServicerContext
from contextvars import ContextVar
from typing import Type, TYPE_CHECKING, Union, Optional, Any
from dataclasses import dataclass
from ...types import StrAnyDict


# Default Request Context Var
class _EmptyRequest: ...


REQUEST_CONTEXT_VAR_TYPE = ContextVar[Union['Request', Type[_EmptyRequest]]]
_current_request: REQUEST_CONTEXT_VAR_TYPE = ContextVar('current_request', default=_EmptyRequest)


@dataclass
class PeerInfo:
    """Store parsed peer information"""
    ip_version: Optional[str] = None
    ip: Optional[str] = None
    port: Optional[int] = None
    raw: Optional[str] = None


class Request:
    """gRPC Request Instance"""

    def __init__(self):
        self.peer_info: PeerInfo = PeerInfo()
        self.metadata: StrAnyDict = {}
        self.package: Optional[str] = None
        self.service_name: Optional[str] = None
        self.method_name: Optional[str] = None
        self.full_method: Optional[str] = None
        self.request_bytes: Optional[bytes] = None
        self.compression: Optional[str] = None
        self.timeout: Optional[float] = None
        self._grpc_context: Optional[ServicerContext] = None
        self.state: StrAnyDict = {}

    @property
    def grpc_context(self) -> ServicerContext:
        return self._grpc_context

    @classmethod
    async def from_grpc_context(cls, context: ServicerContext):
        instance = cls()
        instance._grpc_context = context

        # parse peer
        instance._parse_peer(context.peer())

        # load metadata
        metadata = await context.invocation_metadata()
        instance.metadata = dict(metadata) if metadata else {}

        # parse full_method
        full_method = getattr(context, "_rpc_event", None)
        if full_method and hasattr(full_method, "call_details"):
            instance._parse_method(full_method.call_details.method)

        # parse other
        instance.compression = getattr(context, "compression", lambda: None)()
        instance.timeout = context.time_remaining()

        # inject the current request instance ContextVar
        _current_request.set(instance)
        return instance

    @classmethod
    def current(cls) -> 'Request':
        req = _current_request.get()
        if req is _EmptyRequest:
            raise RuntimeError(
                "Request.current() be invoked, However, there is no Request instance in the current context，"
                "Please ensure that you use it in the gRPC request processing flow."
            )
        return req

    def _parse_peer(self, peer_str: str) -> None:
        """parse peer string"""
        self.peer_info.raw = peer_str
        if not peer_str:
            return

        if peer_str.startswith("ipv4:"):
            m = re.match(r"ipv4:(?P<ip>[^:]+):(?P<port>\d+)", peer_str)
            if m:
                self.peer_info.ip_version = "ipv4"
                self.peer_info.ip = m.group("ip")
                self.peer_info.port = int(m.group("port"))
        elif peer_str.startswith("ipv6:"):
            m = re.match(r"ipv6:\[(?P<ip>[^\]]+)\]:(?P<port>\d+)", peer_str)
            if m:
                self.peer_info.ip_version = "ipv6"
                self.peer_info.ip = m.group("ip")
                self.peer_info.port = int(m.group("port"))
        elif peer_str.startswith("unix:"):
            self.peer_info.ip_version = "unix"
            self.peer_info.ip = peer_str.split(":", 1)[1]
            self.peer_info.port = 0

    def _parse_method(self, full_method: str) -> None:
        """parse full method，eg. /helloworld.Greeter/SayHello"""
        self.full_method = full_method
        if not full_method:
            return

        parts = full_method.strip("/").split("/")
        if len(parts) != 2:
            return

        service_path, method = parts
        self.method_name = method

        # split package & service
        if "." in service_path:
            pkg, svc = service_path.rsplit(".", 1)
            self.package = pkg
            self.service_name = svc
        else:
            self.package = None
            self.service_name = service_path

    def __repr__(self):
        return (
            f"<Request peer={self.peer_info.ip}:{self.peer_info.port} "
            f"service={self.service_name} method={self.method_name} "
            f"metadata={self.metadata}>"
        )
