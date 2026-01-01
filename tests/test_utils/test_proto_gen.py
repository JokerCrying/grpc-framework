import dataclasses
from typing import List, Optional
from src.grpc_framework import GRPCFramework, Service, unary_unary, stream_unary, GRPCFrameworkConfig, StreamRequest
from src.grpc_framework.utils import generate_proto
from src.grpc_framework.core.serialization import DataclassesConverter, DataclassesCodec

@dataclasses.dataclass
class User:
    id: int
    name: str
    tags: List[str]
    email: Optional[str] = None

@dataclasses.dataclass
class CreateUserResponse:
    user: User
    success: bool

class UserService(Service):
    @unary_unary
    def get_user(self, user_id: int) -> User:
        return User(id=user_id, name="Test", tags=[])

    @unary_unary
    def create_user(self, user: User) -> CreateUserResponse:
        return CreateUserResponse(user=user, success=True)

    @stream_unary
    def upload_tags(self, tags: List[str]) -> bool:
        return True


user_small_service = Service('UserSmallService')


@user_small_service.unary_unary
def create_user(request: User) -> CreateUserResponse:
    pass

@user_small_service.stream_stream
def iter_user(request: StreamRequest[User]) -> CreateUserResponse:
    pass

def test_generate_proto():
    app = GRPCFramework(
        config=GRPCFrameworkConfig(
            package='ddd',
            codec=DataclassesCodec,
            converter=DataclassesConverter
        )
    )
    
    app.add_service(UserService)
    app.add_service(user_small_service)
    
    # Add a FBV
    @app.unary_unary
    def health_check(ping: str) -> str:
        return "pong"

    proto_dict = generate_proto(app, auto_mkdir=True)
    
    # Check keys
    assert "UserService" in proto_dict
    assert "RootService" in proto_dict
    
    user_proto = proto_dict["UserService"]
    user_small = proto_dict['UserSmallService']
    root_proto = proto_dict["RootService"]

    print("--- UserService Proto ---")
    print(user_proto)
    print("--- UserSmallService Proto ---")
    print(user_small)
    print("--- RootService Proto ---")
    print(root_proto)
    
    # Assertions for UserService
    assert 'syntax = "proto3";' in user_proto
    assert 'package ddd;' in user_proto
    assert 'service UserService {' in user_proto
    assert 'message User {' in user_proto
    assert 'message CreateUserResponse {' in user_proto
    # Should NOT contain RootService stuff
    assert 'service RootService {' not in user_proto
    assert 'rpc health_check' not in user_proto
    
    # Assertions for RootService
    assert 'syntax = "proto3";' in root_proto
    assert 'package ddd;' in root_proto
    assert 'service RootService {' in root_proto
    assert 'rpc health_check' in root_proto
    # Should NOT contain UserService stuff
    assert 'service UserService {' not in root_proto
    assert 'message User {' not in root_proto  # Unless shared, but here it's clean separation based on impl

if __name__ == "__main__":
    test_generate_proto()
