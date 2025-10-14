from typing import Optional, Sequence, TYPE_CHECKING
from ..utils import Sync2AsyncUtils
from .request.request import Request

if TYPE_CHECKING:
    from ..application import GRPCFramework


class GRPCAdaptor:
    def __init__(self, app: 'GRPCFramework'):
        self.app = app
        self.s2a = Sync2AsyncUtils(self.app.config.executor)

    async def wrap_handler(self):
        with self.app.start_request_context(Request.current()) as ctx:
            pass

    async def wrap_unary_handler(self):
        pass

    async def wrap_unary_stream_handler(self):
        pass

    async def wrap_stream_unary_handler(self):
        pass

    async def wrap_stream_handler(self):
        pass
