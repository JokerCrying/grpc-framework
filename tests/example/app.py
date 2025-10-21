from src.grpc_framework import GRPCFramework, GRPCFrameworkConfig
from tests.example.user_service import UserService
from tests.example.profile_service import service as profile_service

config = GRPCFrameworkConfig.from_module('tests.example.config')
print('config ===', config)

app = GRPCFramework(config=config)
print('application ===', app)

app.add_service(UserService)
app.add_service(profile_service)


@app.unary_unary
def app_uu_func():
    return True


@app.unary_stream
def app_us_func():
    for i in range(1, 11):
        yield i


if __name__ == '__main__':
    print(app._services)
    app.run()
