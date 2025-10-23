<p align="center">
  <img src="./logo.png" alt="grpc-framework">
</p>
<p align="center">
    <em>gRPC Framework，现代gRPC框架，更Pythonic的API接口</em>
</p>

---
**源码地址**: <a href="https://github.com/JokerCrying/grpc-framework" target="_blank">
https://github.com/JokerCrying/grpc-framework
</a>
---

gRPC-Framework是一个现代的、兼容性强、更Pythonic的gRPC框架，用于快速搭建gRPC项目和快速编写gRPC API。

主要特点：

* **Pythonic**:
  通过装饰器驱动的API设计、完整的类型注解支持、多范式编程、异步原生支持和灵活的扩展机制，将复杂的gRPC服务开发简化为符合Python习惯的优雅代码，让开发者能够用最自然的Python方式构建高性能的gRPC项目。
* **现代**: 采用了现代Python的最佳实践，包括原生async/await异步编程、完整的类型注解系统、领域数据建模、contextvars上下文管理和基于装饰器的声明式API设计，完全拥抱了Python
  3.7+的现代特性和设计理念。
* **性能**: 原生异步I/O、可配置的线程池执行器、高效的中间件链式调用、智能的参数解析缓存和基于grpc.aio的底层实现，在保持开发便利性的同时实现了高并发、低延迟的卓越性能表现。
* **兼容性/适配性**:
  简单调用即可无缝兼容传统protoc生成的服务代码，同时支持多种配置格式（YAML、JSON、INI、Python模块）、可插拔的序列化器和编解码器、以及灵活的拦截器和中间件扩展，让开发者能够轻松迁移现有项目并适配各种技术栈需求。
* **简单**: 通过简洁的装饰器语法、零配置的默认设置、直观的类视图和函数视图定义方式，让开发者只需几行代码就能快速构建完整的gRPC服务，将复杂的分布式通信简化为像写普通Python函数一样简单。
* **gRPC标准**: 完全遵循gRPC官方标准，支持四种标准交互模式、protobuf序列化、服务反射、健康检查、拦截器、压缩算法等所有gRPC核心特性，确保与任何标准gRPC客户端和服务端的完全互操作性。
* **客户端支持**: 提供了功能完备的客户端支持，包括智能连接池管理（支持异步和同步模式）、四种标准gRPC调用模式的便捷方法、自动连接维护和预热机制，让开发者能够高效地调用远程gRPC服务并自动管理连接资源。

## 依赖库

gRPC Framework依赖以下几个库开发:

* <a href="https://pypi.org/project/grpcio/" class="external-link" target="_blank">grpcio</a> 提供了标准的grpc通信。
* <a href="https://pypi.org/project/grpcio-reflection/" class="external-link" target="_blank">grpcio-reflection</a>
  提供了标准的grpc反射功能。
* <a href="https://pypi.org/project/grpcio-health-checking/" class="external-link" target="_blank">
  grpcio-health-checking</a> 提供了标准的grpc健康检查功能。
* <a href="https://pypi.org/project/protobuf/" class="external-link" target="_blank">protobuf</a>
  提供了ProtobufMessage类型支持和解析。

## 如何使用

```bash
pip install --upgrade pip
pip install grpc-framework
```

## 配置

gRPC Framework使用单独的配置类去配置，他默认支持了YAML、JSON、INI、Python模块，可通过from_module（Python模块）或from_file（配置文件）或直接实例化创建。

* **<span style="color: red;">*</span>package**: 必填项，它表明了整个grpc应用所运行的包，默认值为grpc，但为grpc时报错。
* **name**: grpc应用程序名称，默认值为grpc-framework。
* **version**: grpc应用程序版本号，建议遵循x.x.x(.beta|alpha)规则
* **host**: grpc应用程序运行地址，若需要运行在全部地址，请使用[::]。
* **port**: grpc应用程序运行端口，默认值为50051。
* **serializer**: 应用全局序列化器，他负责组织Codec和Converter处理请求数据。
* **codec**: 应用全局的Codec，他负责转换请求数据到中间数据，默认为ProtobufCodec。
* **converter**: 应用全局的Converter，他负责转换中间数据到域模型，默认为ProtobufConverter。
* **reflection**: 是否启用grpc反射，默认值为False。
* **app_service_name**: app下函数视图的服务名称，默认为RootService。
* **executor**: 一个Python的Executor类型，可以是ThreadPoolExecutor，也可以是ProcessPoolExecutor，默认为ThreadPoolExecutor(
  max_worker=os.cpu_count() * 2 - 1)。
* **grpc_handlers**: grpc服务可接受的handler类型，默认为None。
* **interceptors**: grpc服务可接受的拦截器类型，默认为None，但服务加载时会加载一个请求解析拦截器。
* **grpc_options**: grpc服务器配置，默认为None，会在应用初始化的时候转为空字典。
* **maximum_concurrent_rpc**: rpc最大请求数，默认为None，表示无限制。
* **grpc_compression**: grpc服务可接受的压缩类型，默认为None。

## 序列化器

gRPC
Framework提供了一个序列化器，他接受两个参数，codec和converter，主要职责是转换请求数据，大致流程是：请求数据（HTTP2数据流） <>
中间数据类型 <> 域模型。
当然，gRPC Framework也提供了一些特定的codec和converter，您可以从grpc_framework中引入，默认提供了:

* **JSONCodec**: 转换bytes为Dict/List类型
* **ProtobufCodec**: 转换bytes为ProtobufMessage类型
* **ORJSONCodec**: 使用orjson库的高性能JSON编解码（<span style="color: red;">*</span>
  这里需要安装orjson依赖才可以使用），主要借用orjson的快速特性。
* **DataclassesCodec**: 转换bytes为Dict/List类型。
* **ProtobufConverter**: ProtobufMessage与域模型间转换（这里是ProtobufMessage的二进制数据）。
* **JsonProtobufConverter**: JSON与ProtobufMessage双向转换。
* **JsonConverter**: JSON字符串与域模型转换。
* **DataclassesConverter**: Dataclass与Dict/List转换（这里是JSONBytes数据）。

### 自定义数据转换

当然，如果gRPC Framework提供的数据类型转换无法支撑您项目中的业务，您也可以自定义序列化器。
您需要实现grpc_framework.TransportCodec或grpc_framework.ModelConverter:

#### Codec

* **decode(self, data: BytesLike, into: OptionalT = None) -> Any**: 实现decode方法，将客户端原始数据转为中间数据类型（transport
  object）
* **encode(self, obj: Any) -> BytesLike**: 实现encode方法，将中间数据类型（transport object）转为bytes类型数据。

```python
class TransportCodec(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def decode(self, data: BytesLike, into: OptionalT = None) -> Any:
        """bytes -> transport object (e.g., protobuf.Message or dict)"""
        raise NotImplementedError

    @abc.abstractmethod
    def encode(self, obj: Any) -> BytesLike:
        """transport object -> bytes"""
        raise NotImplementedError
```

#### Converter

* **to_model(self, transport_obj: Any, model_type: TypeT) -> T**: 转换中间类型（transport object）到域模型
* **from_model(self, model: T) -> Any**: 将域模型转为中间类型（transport object）

```python
class ModelConverter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def to_model(self, transport_obj: Any, model_type: TypeT) -> T:
        """transport object -> domain model"""
        raise NotImplementedError

    @abc.abstractmethod
    def from_model(self, model: T) -> Any:
        """domain model -> transport object"""
        raise NotImplementedError
```

## 例子

<small><span style="color: red;">*</span>例子中使用的Codec和Converter均以JSONCodec和JSONConverter为例</small>

### 创建应用示例和运行

```python
from grpc_framework import GRPCFrameworkConfig, GRPCFramework

config = GRPCFrameworkConfig.from_module('config')

app = GRPCFramework(config=config)

if __name__ == '__main__':
    app.run()
```

### 函数视图

```python
from grpc_framework import GRPCFrameworkConfig, GRPCFramework, Request

config = GRPCFrameworkConfig.from_module('config')

app = GRPCFramework(config=config)


# 第一种写法
@app.unary_unary
def IsServerAlive():
    return {"success": True}


# 第二种写法
from grpc_framework import Service

some_service = Service("SomeService")


@some_service.unary_unary
def GetSomeData():
    # 可以调用request获取本次请求信息
    request = Request.current()
    print(request.metadata)
    return {"success": True, "data": {"id": 1}}


app.add_service(some_service)
```

<details markdown="1">
<summary>或使用 <code>async def</code>...</summary>

```python
from grpc_framework import GRPCFrameworkConfig, GRPCFramework, Request

config = GRPCFrameworkConfig.from_module('config')
app = GRPCFramework(config=config)


# 第一种写法
@app.unary_unary
async def IsServerAlive():
    return {"success": True}


# 第二种写法
from grpc_framework import Service

some_service = Service("SomeService")


@some_service.unary_unary
async def GetSomeData():
    # 可以调用request获取本次请求信息
    request = Request.current()
    print(request.metadata)
    return {"success": True, "data": {"id": 1}}


app.add_service(some_service)
```

</details>

### 类视图

```python
from grpc_framework import GRPCFrameworkConfig, GRPCFramework, Service, unary_unary, stream_unary, StreamRequest

config = GRPCFrameworkConfig.from_module('config')
app = GRPCFramework(config=config)


class SomeService(Service):
    @unary_unary
    def GetSomeData(self):
        # 可以调用request获取本次请求信息
        print(self.request.metadata)
        return {"success": True}

    @stream_unary
    async def sum_counter(self, data: StreamRequest[dict]):
        result = 0
        async for item in data:
            result += data['count']
        return {'result': result}


app.add_service(SomeService)
```

<details markdown="1">
<summary>或使用 <code>async def</code>...</summary>

```python
from grpc_framework import GRPCFrameworkConfig, GRPCFramework, Service, unary_unary, stream_unary, StreamRequest

config = GRPCFrameworkConfig.from_module('config')
app = GRPCFramework(config=config)


class SomeService(Service):
    @unary_unary
    async def GetSomeData(self):
        # 可以调用request获取本次请求信息
        print(self.request.metadata)
        return {"success": True}

    @stream_unary
    async def sum_counter(self, data: StreamRequest[dict]):
        result = 0
        async for item in data:
            result += data['count']
        return {'result': result}


app.add_service(SomeService)
```

</details>

## 旧项目兼容

gRPC Framework提供接口可以兼容之前的旧项目，使用protoc编译得到的服务，可以无缝衔接到gRPC Framework，
但是这样无法使用配置好的请求上下文或中间件，因为只是托管到了应用程序中的服务上，而非完全接管。

### 兼容旧项目例子

```python
import example_pb2
import example_pb2_grpc


class Greeter(example_pb2_grpc.GreeterServicer):
    def say_hello(self, request):
        return example_pb2.HelloReply(message=f"你好，{request.name}")


app.load_rpc_stub(Greeter(), example_pb2_grpc.add_GreeterServicer_to_server)
```

## 客户端支持

gRPC Framework提供了一个客户端，以便使用者可以十分简单的调用grpc服务，他不仅支持使用stub调用，也支持调用指定接口。
同时还提供了一个grpc的Channel连接池，同时支持async生态的channel和默认的channel。

### 连接池配置

* **pool_mode**: 连接池模式，必填项，支持async和default，分别支持async生态的channel管理和默认的channel管理。
* **min_size**: 最小连接数量，默认为10个。
* **max_size**: 最大连接数量，默认为20个。
* **secure_mode**: 是否启用安全模式，他将影响channel创建规则，默认为False。
* **credit**: grpc的安全凭证，若secure_mode=True，该参数不能为空。
* **maintenance_interval**: 每个连接池都会维护一个后台任务去检查每个channel的情况，该参数指定多久检查一次，默认值为5，单位为秒。
* **auto_preheating**: 是否预热连接池，默认为True，开启后每个连接池实例化后都会预热最小链接数量。
* **channel_options**: channel配置。

### 客户端使用

```python
from grpc_framework.client import GRPCChannelPool, GRPCClient, GRPCChannelPoolOptions

grpc_channel_pool = GRPCChannelPool(GRPCChannelPoolOptions(pool_mode='default'))

client = GRPCClient(channel_pool_manager=grpc_channel_pool, host='localhost', port=50051,
                    request_serializer=lambda x: x, response_deserializer=lambda x: x,
                    timeout=5)

# stub调用
import example_pb2_grpc as example_pb2_grpc
import example_pb2 as example_pb2

request = example_pb2.SimpleRequest(query='1', page_number=1, result_per_page=20)
channel = client.channel_pool_manager.get()
impl = example_pb2_grpc.SimpleServiceStub(channel)
resp = client.call_method(impl.GetSimpleResponse, request)
print(resp)

# 指定接口调用
response = client.call_method('/package.Service/Method', request_data=b'{"name":"jack"}')
print(response)
```

## 后续功能清单

| 状态 | 功能描述                | 预计版本   | 备注  |
|----|---------------------|--------|-----|
| ⬜  | 依赖收集                | v1.1.0 | 未开始 |
| ⬜  | 多loop支持             | v1.1.0 | 未开始 |
| ⬜  | 版本支持                | v1.1.0 | 未开始 |
| ⬜  | 服务级别codec/converter | v1.2.0 | 未开始 |
| ⬜  | 服务级别请求上下文           | v1.2.0 | 未开始 |
