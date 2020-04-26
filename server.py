import socket
import selectors
from functools import partial
from threading import RLock
from typing import ByteString

from base import BaseWriter, BaseReader, BaseRequest, BaseHandler
from compress import BaseCompress, default_compress
from default import DefaultReader, DefaultWriter, DefaultHandler

EOF = "\r\n\r\n"


class Server:
    """
    # Running a example
    >>> from server import Server
    >>> server = Server()
    >>> server.run()
    """

    def __init__(self,
                 reader: BaseReader = None,
                 writer: BaseWriter = None,
                 handler: BaseHandler = None,
                 compress: BaseCompress = default_compress,
                 selector=None,
                 port=None,
                 host=None,
                 sock=None,
                 ):
        self._compress = compress

        # i/o multiple selector
        self._selector = selector
        if self._selector is None:
            self._selector = selectors.DefaultSelector()

        # read monitor
        self._reader = reader if reader is not None else DefaultReader(self._compress)

        # write monitor
        self._writer = writer if writer is not None else DefaultWriter(self._compress)

        # check the same compression
        if not isinstance(self._writer.compress, type(self._reader.compress)):
            raise TypeError(
                f"except the same compression class but got {type(self._reader.compress)} and"
                f" {type(self._writer.compress)}")

        # handler
        self._handler = handler if handler is not None else DefaultHandler()

        # server_count
        self._count = 0
        self._lock = RLock()
        self._sock = sock
        self._address = (host or "127.0.0.1", port or 8000)
        if self._sock is None:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind(self._address)

    def __read(self, conn):
        data, request = self._reader(conn=conn)  # type:ByteString,BaseRequest
        if data:
            writer = partial(self.__write, request=request)
            self._selector.unregister(conn)
            try:
                # using lock make persistence would make more bad performance !!! u don't wanna see
                self._selector.register(conn, selectors.EVENT_WRITE, writer)
            except KeyError:
                pass  # FIXME: deal register conflict
        else:
            # no-blocking-call or unknown timeout should unregister the event
            self._selector.unregister(conn)

    def __write(self, conn: socket.socket, request):
        with self._lock:
            self._count += 1
            # TODO: 发送响应包优化
            # FIXME: 优化后头协议如何处理 可以交给tstp处理
            self._writer(conn, request=request, handler=self._handler)
            self._selector.unregister(conn)
            # recursive dependence might occur something terrible
            self._selector.register(conn, selectors.EVENT_READ, self.__read)

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
                # ----  key : SelectorKey = namedtuple('SelectorKey', ['fileobj', 'fd', 'events', 'data'])
                callback = key.data
                callback(key.fileobj)
