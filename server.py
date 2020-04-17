import socket
import selectors
from functools import partial
from threading import RLock
from abc import ABCMeta, abstractmethod
from typing import ByteString, Any, NamedTuple

from compress import default_compress

EOF = "\r\n\r\n"


class BaseRequest(NamedTuple):
    ...


class BaseParser(metaclass=ABCMeta):
    @abstractmethod
    def parser(self, bytes_data: ByteString) -> Any:
        pass


class BaseWriter(metaclass=ABCMeta):

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class BaseReader(metaclass=ABCMeta):

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class Writer(BaseWriter):

    def __call__(self, conn, send_data=None):
        pass


class Reader(BaseReader):

    def __init__(self, parser: BaseParser, request: BaseRequest):
        self._parser = parser
        self._request = request

    def __call__(self, conn):

        data = b''
        while True:
            d = b''
            try:
                d = conn.recv(1024)
            except BlockingIOError:
                pass
            if d:
                data += d
            else:
                break
        parser_data = self.__parser(data)

    def __parser(self, bytes_data: ByteString) -> Any:
        # 做到这里, 有一种要走到 http 的感观, 所以: 是否可以交给使用者自己去定制parser? yes it's OK ！！！
        # 随意、宽泛、自定义 自己定义任何协议, 自己封装请求体
        return self._parser.parser(bytes_data=bytes_data)

    def __deal_data(self, request: BaseRequest) -> ByteString:
        return b''


class Server:

    def __init__(self,
                 reader: BaseReader,  # type
                 writer: BaseWriter,
                 selector=None,
                 port=None,
                 host=None,
                 sock=None,
                 compress=None,

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
        # TODO: no data is error occurred
        if data:
            writer = partial(self._writer.__call__, recv_data=data)
            self._selector.unregister(conn)
            try:
                # 这里可以选择用lock来强一致, 但是会导致并发性能变差
                self._selector.register(conn, selectors.EVENT_WRITE, writer)
            except KeyError:
                pass

    def __write(self, conn: socket.socket, send_data=None):

        with self._lock:
            self._count += 1
            # 逻辑切入点
            # a = 0
            # for i in range(1000):
            #     a += i
            print(f"number: {self._count} " + " ====  echo `", send_data, "`to", conn.getpeername())

            conn.send(self._compress.compress(data=send_data + EOF.encode("utf-8")))

            self._selector.unregister(conn)
            self._selector.register(conn, selectors.EVENT_READ, self.__read)  # 重复依赖会有bug 的可能性
            # conn.close() # TODO: 是否关闭连接

    def __accept(self, sock):
        conn, addr = sock.accept()
        conn.setblocking(False)
        self._selector.register(conn, selectors.EVENT_READ, self.__read)

    def run(self, max_listen=100):
        self._sock.listen(max_listen)
        self._sock.setblocking(False)
        try:
            self._selector.register(self._sock, selectors.EVENT_READ, self.__accept)
        except KeyError:
            pass
        while True:
            events = self._selector.select()
            for key, mask in events:
                # key : SelectorKey = namedtuple('SelectorKey', ['fileobj', 'fd', 'events', 'data'])
                callback = key.data
                callback(key.fileobj)


if __name__ == '__main__':
    s = Server()
    s.run()
