from abc import ABCMeta
from abc import abstractmethod
from typing import ByteString

import zlib


class BaseCompress(metaclass=ABCMeta):
    @abstractmethod
    def compress(self, data: ByteString) -> ByteString:
        if not isinstance(data, bytes):
            raise TypeError(f"except a bytes-like object, but got a {type(data)}")
        return b''

    @abstractmethod
    def decompress(self, data: ByteString) -> ByteString:
        if not isinstance(data, bytes):
            raise TypeError(f"except a bytes-like object, but got a {type(data)}")
        return b''


class ZlibCompress(BaseCompress):
    def __init__(self, compress_level: int = 5):
        self.compress_level = compress_level

    def compress(self, data: ByteString) -> ByteString:
        super().compress(data)
        return zlib.compress(data, level=self.compress_level)

    def decompress(self, data: ByteString) -> ByteString:
        super().decompress(data)
        # need do more thing
        return zlib.decompress(data)


default_compress = ZlibCompress()
