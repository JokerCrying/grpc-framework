from src.grpc_framework import GRPCFramework, GRPCFrameworkConfig

config = GRPCFrameworkConfig(
    package='test-many-worker',
    workers=4
)

app = GRPCFramework(config=config)

if __name__ == '__main__':
    app.run()
