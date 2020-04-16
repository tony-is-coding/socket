import socket
import selectors
from functools import partial
from threading import RLock
from abc import ABCMeta, abstractmethod

EOF = "\r\n\r\n"


class Server:

    def __init__(self,
                 selector=None,
                 port=None,
                 host=None,
                 sock=None
                 ):
        self._selector = selector
        if self._selector is None:
            self._selector = selectors.DefaultSelector()
        self._count = 0
        self._lock = RLock()
        self._sock = sock
        self._address = (host or "127.0.0.1", port or 8001)
        if self._sock is None:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind(self._address)

    def __read(self, conn, mask):
        # 这里可以选择用lock来强一致, 但是会导致并发性能变差

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
        if data:
            writer = partial(self.__write, send_data=data)
            self._selector.unregister(conn)
            try:
                self._selector.register(conn, selectors.EVENT_WRITE, writer)
            except KeyError:
                pass

    def __write(self, conn: socket.socket, mask, send_data=None):

        with self._lock:
            self._count += 1
            a = 0
            # for i in range(1000):
            #     a += i
            print(f"number: {self._count} " + " ====  echo `", send_data, "`to", conn.getpeername())
            conn.send(send_data + EOF.encode("utf-8"))
            self._selector.unregister(conn)
            self._selector.register(conn, selectors.EVENT_READ, self.__read)
            # conn.close()

    def __accept(self, sock, mask):
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
                callback = key.data
                callback(key.fileobj, mask)


class BaseWriter(metaclass=ABCMeta):

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass

    @abstractmethod
    def write(self):
        pass


class BaseReader(metaclass=ABCMeta):
    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass

    @abstractmethod
    def read(self):
        pass


class Reader(BaseReader):
    def __call__(self, *args, **kwargs):
        pass

    def read(self):
        pass



if __name__ == '__main__':
    s = Server()
    s.run()
