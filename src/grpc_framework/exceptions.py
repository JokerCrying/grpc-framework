import grpc
from .core.request.request import Request


class GRPCException(Exception):
    """
    gRPC 服务异常类，提供便捷方法创建特定类型的 gRPC 异常
    """

    def __init__(
            self,
            code: grpc.StatusCode,
            detail: str,
            **kwargs
    ):
        """
        初始化 GRPCException

        :param code: gRPC 状态码
        :param detail: 错误详情
        :param debug_info: 调试信息
        :param retry_info: 重试信息
        :param kwargs: 其他自定义参数
        """
        super().__init__(detail)
        self.code = code
        self.detail = str(detail)
        self.request = Request.current()
        self.kwargs = kwargs

    # 类方法工厂
    @classmethod
    def cancelled(cls, detail: str, **kwargs) -> 'GRPCException':
        return cls(grpc.StatusCode.CANCELLED, detail, **kwargs)

    @classmethod
    def unknown(cls, detail: str, **kwargs) -> 'GRPCException':
        return cls(grpc.StatusCode.UNKNOWN, detail, **kwargs)

    @classmethod
    def invalid_argument(cls, detail: str, **kwargs) -> 'GRPCException':
        return cls(grpc.StatusCode.INVALID_ARGUMENT, detail, **kwargs)

    @classmethod
    def deadline_exceeded(cls, detail: str, **kwargs) -> 'GRPCException':
        return cls(grpc.StatusCode.DEADLINE_EXCEEDED, detail, **kwargs)

    @classmethod
    def not_found(cls, detail: str, **kwargs) -> 'GRPCException':
        return cls(grpc.StatusCode.NOT_FOUND, detail, **kwargs)

    @classmethod
    def already_exists(cls, detail: str, **kwargs) -> 'GRPCException':
        return cls(grpc.StatusCode.ALREADY_EXISTS, detail, **kwargs)

    @classmethod
    def permission_denied(cls, detail: str, **kwargs) -> 'GRPCException':
        return cls(grpc.StatusCode.PERMISSION_DENIED, detail, **kwargs)

    @classmethod
    def unauthenticated(cls, detail: str, **kwargs) -> 'GRPCException':
        return cls(grpc.StatusCode.UNAUTHENTICATED, detail, **kwargs)

    @classmethod
    def resource_exhausted(cls, detail: str, **kwargs) -> 'GRPCException':
        return cls(grpc.StatusCode.RESOURCE_EXHAUSTED, detail, **kwargs)

    @classmethod
    def failed_precondition(cls, detail: str, **kwargs) -> 'GRPCException':
        return cls(grpc.StatusCode.FAILED_PRECONDITION, detail, **kwargs)

    @classmethod
    def aborted(cls, detail: str, **kwargs) -> 'GRPCException':
        return cls(grpc.StatusCode.ABORTED, detail, **kwargs)

    @classmethod
    def out_of_range(cls, detail: str, **kwargs) -> 'GRPCException':
        return cls(grpc.StatusCode.OUT_OF_RANGE, detail, **kwargs)

    @classmethod
    def unimplemented(cls, detail: str, **kwargs) -> 'GRPCException':
        return cls(grpc.StatusCode.UNIMPLEMENTED, detail, **kwargs)

    @classmethod
    def internal(cls, detail: str, **kwargs) -> 'GRPCException':
        return cls(grpc.StatusCode.INTERNAL, detail, **kwargs)

    @classmethod
    def unavailable(cls, detail: str, **kwargs) -> 'GRPCException':
        return cls(grpc.StatusCode.UNAVAILABLE, detail, **kwargs)

    @classmethod
    def data_loss(cls, detail: str, **kwargs) -> 'GRPCException':
        return cls(grpc.StatusCode.DATA_LOSS, detail, **kwargs)
