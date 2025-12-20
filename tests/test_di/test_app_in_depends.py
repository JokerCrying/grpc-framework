from src.grpc_framework import (
    GRPCFramework, GRPCFrameworkConfig,
    Depends, JSONCodec, JsonConverter,
    Service, unary_unary, unary_stream
)

cfg = GRPCFrameworkConfig(
    package='test',
    codec=JSONCodec,
    converter=JsonConverter,
    workers=4
)
app = GRPCFramework(cfg)


# --- Dependencies ---
class RedisConnect:
    def __init__(self):
        self.client = '<RedisClient url=redis://:@localhost:6379>'


app.container.register(RedisConnect, RedisConnect)


async def get_db():
    yield "db_connection"


def get_config():
    return {"debug": True}


async def get_service(
        db: str = Depends(get_db),
        config: dict = Depends(get_config)
):
    return f"Service(db={db}, debug={config['debug']})"


# --- CBV Service ---
class UserService(Service):
    redis: Depends[RedisConnect]
    redis2: RedisConnect = Depends(RedisConnect)

    @unary_unary
    async def redis_test(self):
        return {'result': self.redis.client}

    @unary_unary
    async def redis_test2(self):
        return {'result': self.redis2.client}

    @unary_unary
    async def get_user(
            self,
            service: str = Depends(get_service)
    ):
        return {"id": 1, "service": service}

    @unary_stream
    async def stream_users(
            self,
            db: str = Depends(get_db)
    ):
        yield {"name": f"{'d'}_1", "source": db}
        yield {"name": f"{'d'}_2", "source": db}


# --- FBV Handlers ---
@app.unary_unary
async def health_check(
        db: str = Depends(get_db)
):
    return {"status": "ok", "db": db}


@app.unary_unary
async def complex_op(
        service: str = Depends(get_service)
):
    return {"result": service}


@app.unary_unary
async def redis(
        redis_client: Depends[RedisConnect]
):
    return {'result': redis_client.client}


app.add_service(UserService)
if __name__ == '__main__':
    app.run()
