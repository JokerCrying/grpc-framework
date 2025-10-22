import uuid
from dataclasses import dataclass
from src.grpc_framework import Service
from src.grpc_framework import StreamRequest

service = Service('ProfileService')


@dataclass
class Profile:
    name: str


@dataclass
class ProfileIterCounter:
    counter: int


@dataclass
class StreamIterCounter:
    counter: int


@dataclass
class StreamIterCountResponse:
    count: int


@dataclass
class SimulateChatRequest:
    user_id: int
    to_user_id: int
    message: str
    message_type: str


@dataclass
class SimulateChatResponse:
    success: bool
    message: str


@service.unary_unary
async def get_profile():
    return Profile(name=str(uuid.uuid4()))


@service.unary_stream
async def iter_profile_counter(counter: ProfileIterCounter):
    for i in range(1, counter.counter + 1):
        yield Profile(name=str(uuid.uuid4()))


@service.stream_unary
async def sum_counter(request: StreamRequest[StreamIterCounter]):
    result = 0
    async for item in request:
        result += item.counter
    return StreamIterCountResponse(count=result)


@service.stream_stream
async def simulated_chat(request: StreamRequest[SimulateChatRequest]):
    async for chat in request:
        print(f'user({chat.user_id}) send ({chat.message_type}) to user({chat.to_user_id}): {chat.message}')
        yield SimulateChatResponse(success=True, message=chat.message)
