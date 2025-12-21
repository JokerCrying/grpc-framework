from src.grpc_framework import Depends, GRPCFramework, GRPCFrameworkConfig, Request, Service, unary_unary, JsonConverter, JSONCodec
from dataclasses import asdict

app = GRPCFramework(
    GRPCFrameworkConfig(
        package='test',
        codec=JSONCodec,
        converter=JsonConverter
    )
)


class Impl:
    def __init__(self):
        self.request = Request.current()

    async def get_peer_info(self):
        return asdict(self.request.peer_info)


class UserService(Service):
    impl: Impl = Depends(Impl)

    @unary_unary
    async def get_peer(self):
        return await self.impl.get_peer_info()


app.add_service(UserService)

if __name__ == '__main__':
    app.run()
