"""gRPC框架

提供简洁优雅的API设计体验，支持依赖注入、中间件、拦截器等现代化功能。

基本用法:
    from grpc_framework import GRPCFramework, Depends

    app = GRPCFramework("my_service")

    app.register_service(MyServicer)  # cbv

    app.register_service(my_service)  # fbv

    app.start(port=50051)
"""

__version__ = "0.0.1"
__author__ = "surp1us"
__description__ = "gRPC framework for Python"
