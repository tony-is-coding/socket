import socket
import selectors
from functools import partial
from threading import RLock
from abc import ABCMeta, abstractmethod
from typing import ByteString, NamedTuple, Union, AnyStr, List, Dict, Tuple, Set
import struct

from compress import default_compress

EOF = "\r\n\r\n"
PyObject = Union[Set, Tuple, List, Dict, AnyStr, int]


class BaseRequest(NamedTuple):
    pass


class DefaultRequest(BaseRequest):
    data: str
    keep_alive: int


class BaseParser(metaclass=ABCMeta):
    @abstractmethod
    def decode(self, bytes_data: ByteString) -> PyObject:
        pass

    @abstractmethod
    def encode(self, data: PyObject) -> ByteString:
        pass


class BaseWriter(metaclass=ABCMeta):

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class BaseReader(metaclass=ABCMeta):

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class DefaultWriter(BaseWriter):

    def __call__(self, conn, send_data=None):
        pass


class DefaultReader(BaseReader):

    def __init__(self, parser: BaseParser = None, request: BaseRequest = None):
        self._parser = parser
        self._request = request
        self._buffer_size = 256

    def __call__(self, conn) -> ByteString:
        print(f"read from {conn}")
        data = b''
        while True:
            try:
                d = conn.recv(4)
                if not d:
                    break
                cl = struct.unpack('I', d)[0]
                while cl > 0:
                    if cl > self._buffer_size:
                        d = conn.recv(self._buffer_size)
                        data += d
                        cl -= self._buffer_size
                    else:
                        d = conn.recv(cl)
                        data += d
                        cl = 0
                break
            except BlockingIOError:  # 非阻塞socket调用了 阻塞的方法
                pass
            except ConnectionResetError:  # 注册事件的socket 断开了连接
                pass
        if data:
            print(data.decode("utf-8"))
            parser_data = self.__parser(data)
            return self.__deal_data(parser_data)
        else:
            return b''

    def __parser(self, bytes_data: ByteString) -> BaseRequest:
        # 做到这里, 有一种要走到 http 的感观, 所以: 是否可以交给使用者自己去定制parser? yes it's OK ！！！
        # 随意、宽泛、自定义 自己定义任何协议, 自己封装请求体
        # return self._parser.decode(bytes_data=bytes_data)
        return BaseRequest()

    def __deal_data(self, request: BaseRequest) -> ByteString:
        # handler logic
        return b'has received data'


class Server:

    def __init__(self,
                 reader: BaseReader,  # type
                 writer: BaseWriter,
                 selector=None,
                 port=None,
                 host=None,
                 sock=None,
                 compress=None
                 ):

        # bit compression
        self._compress = compress
        if self._compress is None:
            self._compress = default_compress

        # i/o multiple selector
        self._selector = selector
        if self._selector is None:
            self._selector = selectors.DefaultSelector()

        # read monitor
        self._reader = reader

        # write monitor
        self._writer = writer

        # server_count
        self._count = 0
        self._lock = RLock()
        self._sock = sock
        self._address = (host or "127.0.0.1", port or 8001)
        if self._sock is None:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind(self._address)

    def __read(self, conn):
        data = self._reader(conn=conn)
        if data:
            writer = partial(self.__write, send_data=data)
            self._selector.unregister(conn)
            try:
                # 这里可以选择用lock来强一致, 但是会导致并发性能变差
                self._selector.register(conn, selectors.EVENT_WRITE, writer)
            except KeyError:
                pass
        else:
            # 非阻塞调用 或者 超时断开需要取消注册
            self._selector.unregister(conn)

    def __write(self, conn: socket.socket, send_data=None):
        with self._lock:
            self._count += 1
            # 逻辑切入点
            # a = 0
            # for i in range(1000):
            #     a += i
            print(f"number: {self._count} " + " ====  echo `", send_data, "`to", conn.getpeername())

            # TODO: 发送响应包优化
            # FIXME: 优化后头协议如何处理 可以交给tstpq处理
            # conn.send(self._compress.compress(data=send_data + EOF.encode("utf-8")))
            conn.send(send_data + EOF.encode("utf-8"))
            self._writer(conn, send_data)
            self._selector.unregister(conn)
            self._selector.register(conn, selectors.EVENT_READ, self.__read)  # 重复依赖会有bug 的可能性
            # conn.close()

    def __accept(self, sock):
        conn, addr = sock.accept()
        print(f"create connect -- {conn}")
        conn.setblocking(False)
        self._selector.register(conn, selectors.EVENT_READ, self.__read)

    def run(self, max_listen=100):
        self._sock.listen(max_listen)
        self._sock.setblocking(False)
        try:
            self._selector.register(self._sock, selectors.EVENT_READ, self.__accept)
        except KeyError as e:
            print(str(e))
        while True:
            events = self._selector.select()
            for key, mask in events:
                # key : SelectorKey = namedtuple('SelectorKey', ['fileobj', 'fd', 'events', 'data'])
                callback = key.data
                callback(key.fileobj)


if __name__ == '__main__':
    server = Server(reader=DefaultReader(), writer=DefaultWriter(), port=8000)
    server.run()
