import grpc
from typing import TYPE_CHECKING, Tuple, Any
from ..response.response import Response
from ..request.request import Request
from ...utils.reactive_context import AsyncReactiveContext
from ...exceptions import GRPCException

if TYPE_CHECKING:
    from ...application import GRPCFramework


class _Empty: pass  # Lightweight Marking


class ResponseAdaptor:
    def __init__(
            self,
            app: 'GRPCFramework',
            response: Response,
            request: Request,
            ctx: AsyncReactiveContext
    ):
        self.app = app
        self.original_response = response  # retain the original response
        self.request = request
        self.ctx = ctx

    async def get_response(self) -> bytes:
        """
        main entrance：Uniformly process the response and return the byte content that is ultimately to be sent to the gRPC client
        """
        try:
            # Step 1: handle whether the handler throws an exception
            if isinstance(self.original_response.content, Exception):
                error_resp, content = self._build_error_response_from_handler_exception(
                    self.original_response.content
                )
            else:
                # Step 2: try to render a normal response
                rendered = self._safe_render()
                if rendered is _Empty:
                    # success
                    error_resp, content = self._build_error_response_from_render_failure()
                else:
                    # fail
                    error_resp = None
                    content = rendered

            # Step 3: send response context events
            if error_resp:
                await self.ctx.send(error_resp)
                await self.call_error_handler(error_resp.content)
                return b''
            else:
                # a successful response also requires sending (for middleware use).
                success_resp = Response(
                    content=self.original_response.content,
                    status_code=grpc.StatusCode.OK,
                    app=self.app
                )
                await self.ctx.send(success_resp)
                return content

        except Exception as unexpected:
            # bottom line protection
            fallback_resp = Response(
                content=unexpected,
                status_code=grpc.StatusCode.INTERNAL,
                app=self.app
            )
            await self.ctx.send(fallback_resp)
            await self.call_error_handler(unexpected)
            return b''

    def _safe_render(self) -> Any | _Empty:
        """safe rendering failed and returned _Empty"""
        try:
            return self.original_response.render()
        except Exception as e:
            self.app.logger.exception("Response rendering failed")
            self.app.logger.exception(e)
            return _Empty

    def _build_error_response_from_handler_exception(
            self, exc: Exception
    ) -> Tuple[Response, bytes]:
        if isinstance(exc, GRPCException):
            code = exc.code
        else:
            code = grpc.StatusCode.INTERNAL
        error_resp = Response(content=exc, status_code=code, app=self.app)
        return error_resp, b''

    def _build_error_response_from_render_failure(self) -> Tuple[Response, bytes]:
        exc = GRPCException.internal("Failed to serialize response")
        error_resp = Response(content=exc, status_code=grpc.StatusCode.INTERNAL, app=self.app)
        return error_resp, b''

    async def call_error_handler(self, exc: Exception):
        await self.app._error_handler.call_error_handler(exc, self.request)
