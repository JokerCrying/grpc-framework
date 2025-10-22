import unittest
import dataclasses
from src.grpc_framework import Serializer, DataclassesCodec, DataclassesConverter


@dataclasses.dataclass
class User:
    id: int
    name: str


class TestDataclass(unittest.TestCase):
    def setUp(self):
        self.s = Serializer(DataclassesCodec, DataclassesConverter)
        self.original_data = b'{"id":2,"name":"Jack"}'
        self.instance = User(id=1, name='Tom')

    def test_transport(self):
        bytes_data = self.s.serialize(self.instance)
        print(bytes_data)

    def test_make(self):
        r = self.s.deserialize(self.original_data, User)
        print(r)
