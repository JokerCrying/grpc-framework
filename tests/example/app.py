from typing import Callable
import tests.example_grpc_proto.example_pb2_grpc as example_pb2_grpc
import tests.example_grpc_proto.example_pb2 as example_pb2
from dataclasses import dataclass
from src.grpc_framework import GRPCFramework, GRPCFrameworkConfig, BaseMiddleware, Request
from tests.example.user_service import UserService
from tests.example.profile_service import service as profile_service


class SimpleService(example_pb2_grpc.SimpleServiceServicer):
    def GetSimpleResponse(self, reqeust, context):
        return example_pb2.SimpleResponse(result='success', success=True, error_message='')

    def StreamResponses(self, request, context):
        yield example_pb2.SimpleResponse(result='success', success=True, error_message='')


class LoggerMiddleware(BaseMiddleware):

    async def dispatch(self, request: Request, call_next: Callable):
        print('received the request ->', request)
        return await call_next(request)


config = GRPCFrameworkConfig.from_module('tests.example.config')

app = GRPCFramework(config=config)

app.add_middleware(LoggerMiddleware)

app.add_service(UserService)
app.add_service(profile_service)
app.load_rpc_stub(SimpleService, example_pb2_grpc.add_SimpleServiceServicer_to_server)


@dataclass
class Domain:
    id: int


@app.unary_unary
def app_uu_func():
    return Domain(id=1)


@app.unary_stream
def app_us_func():
    for i in range(1, 11):
        yield Domain(id=i)


if __name__ == '__main__':
    app.run()
