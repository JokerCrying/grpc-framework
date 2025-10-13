import unittest
from src.grpc_framework.application import GRPCFramework, Interaction

app = GRPCFramework()


@app.method(Interaction.unary, Interaction.unary)
def create_user():
    pass


class TestAppFBV(unittest.TestCase):
    def test_app_fbv(self):
        print(app._services)
