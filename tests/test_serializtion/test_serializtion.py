import unittest
import tests.test_serializtion.test_pb2 as test_pb2
from src.grpc_framework.core import Serializer, JSONCodec, JsonProtobufConverter

# bash: python -m grpc_tools.protoc --python_out=. --grpc_python_out=. --proto_path=. ./test.proto
class TestSerialization(unittest.TestCase):
    def test_serialization(self):
        data = test_pb2.UserTest(name='Jack', id=1, email='admin@a.com')
        print('original data ===', data)
        serializer = Serializer(JSONCodec, JsonProtobufConverter)
        print('serializer ===', serializer)
        transport_data = serializer.serialize(data)
        print('transport data ===', transport_data)
        deserialization_data = serializer.deserialize(transport_data, test_pb2.UserTest)
        print('deserialization data ===', deserialization_data)
        assert deserialization_data == data, 'Has different data was deserialization.'


