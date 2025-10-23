import abc
import grpc
import time
import random
import asyncio
import threading
import grpc.aio as grpc_aio
from dataclasses import dataclass
from typing import Optional, Dict, Set, Any, Literal, Union


@dataclass
class GRPCChannelPoolOptions:
    pool_mode: Literal['async', 'default']
    min_size: Optional[int] = 10
    max_size: Optional[int] = 20
    secure_mode: Optional[bool] = False
    credit: Optional[grpc.ChannelCredentials] = None
    maintenance_interval: Optional[int] = 5
    auto_preheating: Optional[bool] = True
    channel_options: Optional[Dict[str, Any]] = None


class IChannelPool(metaclass=abc.ABCMeta):
    """grpc channel pool interface"""

    def __init__(self, min_size: int, max_size: int, host: str, port: int, maintenance_interval: int,
                 auto_preheating: bool, channel_options: Dict[str, Any], secure_mode: Optional[bool],
                 credit: Optional[grpc.ChannelCredentials]):
        self.min_size = min_size
        self.max_size = max_size
        self.host = host
        self.port = port
        self._address = f"{host}:{port}"
        self._channels: Set[Union[grpc.Channel, grpc_aio.Channel]] = set()
        self.maintenance_interval = maintenance_interval
        self.channel_options = channel_options
        self.secure_mode = secure_mode
        self.credit = credit
        self.task = None
        self.start_maintenance_task()
        if self.task is None:
            raise RuntimeError('set a value to `self.task` when implemented start_maintenance_task.')
        if auto_preheating:
            self.preheating_channels()

    @abc.abstractmethod
    def channel_factory(self, address: str):
        raise NotImplementedError

    @abc.abstractmethod
    def start_maintenance_task(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self):
        raise NotImplementedError

    def preheating_channels(self):
        self._channels = set([
            self.channel_factory(self._address)
            for _ in range(self.min_size)
        ])

    def _remove_channel(self, channel: Union[grpc_aio.Channel, grpc.Channel]):
        self._channels.remove(channel)

    def _add_channel(self):
        if len(self._channels) <= self.max_size:
            self._channels.add(self.channel_factory(self._address))


class AsyncChannelPool(IChannelPool):
    """async grpc channel pool, support multiplexing"""

    async def _task(self):
        while True:
            remove_useless_channels = []
            for channel in self._channels:
                if channel.get_state(try_to_connect=True) in [
                    grpc.ChannelConnectivity.SHUTDOWN,
                    grpc.ChannelConnectivity.TRANSIENT_FAILURE,
                ]:
                    remove_useless_channels.append(channel)
            for i in range(len(remove_useless_channels)):
                self._remove_channel(remove_useless_channels[i])
                self._add_channel()
            await asyncio.sleep(self.maintenance_interval)

    def start_maintenance_task(self):
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self._task())

    def channel_factory(self, address: str):
        if self.secure_mode:
            if self.credit is None:
                raise ValueError('When using secure mode, please pass the `credit` field in the channel options')
            return grpc_aio.secure_channel(address, self.credit, self.channel_options)
        else:
            return grpc_aio.insecure_channel(
                address, self.channel_options
            )

    def get(self):
        if not self._channels:
            return None
        channel: grpc_aio.Channel = random.choice(list(self._channels))
        if channel.get_state(try_to_connect=True) in [
            grpc.ChannelConnectivity.SHUTDOWN,
            grpc.ChannelConnectivity.TRANSIENT_FAILURE,
        ]:
            self._remove_channel(channel)
            self._add_channel()
            return self.get()
        return channel


class ChannelPool(IChannelPool):
    """default grpc channel pool, support multiplexing"""

    def _task(self):
        while True:
            remove_useless_channels = []
            for channel in self._channels:
                if self.get_channel_state(channel) in [
                    grpc.ChannelConnectivity.SHUTDOWN,
                    grpc.ChannelConnectivity.TRANSIENT_FAILURE,
                ]:
                    remove_useless_channels.append(channel)
            for i in range(len(remove_useless_channels)):
                self._remove_channel(remove_useless_channels[i])
                self._add_channel()
            time.sleep(self.maintenance_interval)

    def channel_factory(self, address: str):
        if self.secure_mode:
            if self.credit is None:
                raise ValueError('When using secure mode, please pass the `credit` field in the channel options')
            return grpc.secure_channel(address, self.credit, self.channel_options)
        else:
            return grpc.insecure_channel(
                address, self.channel_options
            )

    def start_maintenance_task(self):
        self.task = threading.Thread(target=self._task, daemon=True)
        self.task.start()

    def get(self):
        if not self._channels:
            return None
        channel: grpc.Channel = random.choice(list(self._channels))
        if self.get_channel_state(channel) in [
            grpc.ChannelConnectivity.SHUTDOWN,
            grpc.ChannelConnectivity.TRANSIENT_FAILURE,
        ]:
            self._remove_channel(channel)
            self._add_channel()
            return self.get()
        return channel

    @staticmethod
    def get_channel_state(channel: grpc.Channel):
        """get grpc default channel"""
        state = channel._channel.check_connectivity_state(True)
        if state == 0:
            return grpc.ChannelConnectivity.IDLE
        elif state == 1:
            return grpc.ChannelConnectivity.CONNECTING
        elif state == 2:
            return grpc.ChannelConnectivity.READY
        elif state == 3:
            return grpc.ChannelConnectivity.TRANSIENT_FAILURE
        elif state == 4:
            return grpc.ChannelConnectivity.SHUTDOWN
        else:
            return grpc.ChannelConnectivity.SHUTDOWN


class GRPCChannelPool:
    """global grpc connection pool manager"""

    def __init__(
            self,
            config: GRPCChannelPoolOptions
    ):
        if config.pool_mode == 'async':
            pool_class = AsyncChannelPool
        elif config.pool_mode == 'default':
            pool_class = ChannelPool
        else:
            raise ValueError('Only two connection pool modes, async and default, are supported.')
        self._pool_class = pool_class
        self._min_size = config.min_size or 10
        self._max_size = config.max_size or 10
        self._maintenance_interval = config.maintenance_interval or 5
        self._auto_preheating = config.auto_preheating or True
        self._pools: Dict[str, IChannelPool] = {}
        self._secure_mode = config.secure_mode or False
        self._credit = config.credit or None
        self._channel_options = config.channel_options or {}

    def get(self, host: str = 'localhost', port: int = 50051) -> Optional[Union[grpc_aio.Channel, grpc.Channel]]:
        """the channel for obtaining the specified service"""
        key = f"{host}:{port}"
        # get or create a connection pool
        if key not in self._pools:
            self._pools[key] = self._pool_class(
                min_size=self._min_size,
                max_size=self._max_size,
                host=host,
                port=port,
                maintenance_interval=self._maintenance_interval,
                auto_preheating=self._auto_preheating,
                secure_mode=self._secure_mode,
                credit=self._credit,
                channel_options=self._channel_options
            )
        # 从池中获取通道
        return self._pools[key].get()
