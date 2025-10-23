<p align="center">
  <img src="./logo.png" alt="grpc-framework">
</p>
<p align="center">
    <em>gRPC Framework，现代gRPC框架，更Pythonic的API接口</em>
</p>

---
**源码地址**: <a href="https://github.com/JokerCrying/grpc-framework" target="_blank">https://github.com/JokerCrying/grpc-framework</a>
---

gRPC-Framework是一个现代的、兼容性强、更Pythonic的gRPC框架，用于快速搭建gRPC项目和快速编写gRPC API。

主要特点：
* **Pythonic**: 通过装饰器驱动的API设计、完整的类型注解支持、多范式编程、异步原生支持和灵活的扩展机制，将复杂的gRPC服务开发简化为符合Python习惯的优雅代码，让开发者能够用最自然的Python方式构建高性能的gRPC项目。
* **现代**: 采用了现代Python的最佳实践，包括原生async/await异步编程、完整的类型注解系统、领域数据建模、contextvars上下文管理和基于装饰器的声明式API设计，完全拥抱了Python 3.7+的现代特性和设计理念。
* **性能**: 原生异步I/O、可配置的线程池执行器、高效的中间件链式调用、智能的参数解析缓存和基于grpc.aio的底层实现，在保持开发便利性的同时实现了高并发、低延迟的卓越性能表现。
* **兼容性/适配性**: 简单调用即可无缝兼容传统protoc生成的服务代码，同时支持多种配置格式（YAML、JSON、INI、Python模块）、可插拔的序列化器和编解码器、以及灵活的拦截器和中间件扩展，让开发者能够轻松迁移现有项目并适配各种技术栈需求。
* **简单**: 通过简洁的装饰器语法、零配置的默认设置、直观的类视图和函数视图定义方式，让开发者只需几行代码就能快速构建完整的gRPC服务，将复杂的分布式通信简化为像写普通Python函数一样简单。
* **gRPC标准**: 完全遵循gRPC官方标准，支持四种标准交互模式、protobuf序列化、服务反射、健康检查、拦截器、压缩算法等所有gRPC核心特性，确保与任何标准gRPC客户端和服务端的完全互操作性。
* **客户端支持**: 提供了功能完备的客户端支持，包括智能连接池管理（支持异步和同步模式）、四种标准gRPC调用模式的便捷方法、自动连接维护和预热机制，让开发者能够高效地调用远程gRPC服务并自动管理连接资源。

## 依赖库
gRPC Framework依赖以下几个库开发: 

* <a href="https://pypi.org/project/grpcio/" class="external-link" target="_blank">grpcio</a> 提供了标准的grpc通信。
* <a href="https://pypi.org/project/grpcio-reflection/" class="external-link" target="_blank">grpcio-reflection</a> 提供了标准的grpc反射功能。
* <a href="https://pypi.org/project/grpcio-health-checking/" class="external-link" target="_blank">grpcio-health-checking</a> 提供了标准的grpc健康检查功能。
* <a href="https://pypi.org/project/protobuf/" class="external-link" target="_blank">protobuf</a> 提供了ProtobufMessage类型支持和解析。

## 如何使用
```bash
pip install --upgrade
pip install grpc-framework
```

## 序列化器
gRPC Framework提供了一个序列化器，他接受两个参数，codec和converter，主要职责是转换请求数据，大致流程是：请求数据（HTTP2数据流） <> 中间数据类型 <> 域模型。
当然，gRPC Framework也提供了一些特定的codec和converter，您可以从grpc_framework中引入，默认提供了:
* **JSONCodec**: 转换bytes为Dict/List类型
* **ProtobufCodec**: 转换bytes为ProtobufMessage类型
* **ORJSONCodec**: 使用orjson库的高性能JSON编解码（<span style="color: red;">*</span>这里需要安装orjson依赖才可以使用），主要借用orjson的快速特性。
* **DataclassesCodec**: 转换bytes为Dict/List类型。
* **ProtobufConverter**: ProtobufMessage与域模型间转换（这里是ProtobufMessage的二进制数据）。
* **JsonProtobufConverter**: JSON与ProtobufMessage双向转换。
* **JsonConverter**: JSON字符串与域模型转换。
* **DataclassesConverter**: Dataclass与Dict/List转换（这里是JSONBytes数据）。

### 自定义数据转换
当然，如果gRPC Framework提供的数据类型转换无法支撑您项目中的业务，您也可以自定义序列化器。
您需要实现grpc_framework.TransportCodec或grpc_framework.ModelConverter: 

#### Codec
* **decode(self, data: BytesLike, into: OptionalT = None) -> Any**: 实现decode方法，将客户端原始数据转为中间数据类型（transport object）
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


## 后续功能清单
| 状态 | 功能描述 | 预计版本   | 备注  |
|-----|--|--------|-----|
| ⬜ | 依赖收集 | v1.1.0 | 未开始 |
| ⬜ | 多loop支持 | v1.1.0 | 未开始 |
