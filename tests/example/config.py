from src.grpc_framework import DataclassesCodec, DataclassesConverter

name = 'grpc-framework-demo'

version = '1.0.0.beta'

host = '[::]'

port = 50051

reflection = True

add_health_check = True

app_service_name = 'GRPCFrameWorkDemoService'

codec = DataclassesCodec

converter = DataclassesConverter
