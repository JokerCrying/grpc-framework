from dataclasses import dataclass
from src.grpc_framework import GRPCFramework, GRPCFrameworkConfig
from tests.example.user_service import UserService
from tests.example.profile_service import service as profile_service

config = GRPCFrameworkConfig.from_module('tests.example.config')

app = GRPCFramework(config=config)

app.add_service(UserService)
app.add_service(profile_service)


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
