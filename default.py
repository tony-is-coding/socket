import struct
from typing import ByteString, Tuple

from base import BaseReader, BaseWriter, BaseRequest, BaseHandler, BaseResponse
from compress import BaseCompress, default_compress
from typevars import Header, Body


class DefaultRequest(BaseRequest):
    def __init__(self, header: Header = Header(content_length=0), body: Body = b''):
        self._header = header
        self._body = body

    def header(self) -> Header:
        return self._header

    def set_header(self, **kwargs):
        """
        something useful for content parser and connect manage
        - headers
            -- content_length：body length
        """
        # TODO: extend header fields
        cl = kwargs.get("content_length")
        if cl is not None:
            self._header.content_length = cl

    def body(self) -> Body:
        return self._body

    def set_body(self, body: ByteString):
        self._body = body

    def append_body(self, tail: ByteString):
        self._body += tail


class DefaultResponse(BaseResponse):

    def __init__(self, header: Header = Header(content_length=0), body: Body = b''):
        self._header = header
        self._body = body

    def body(self) -> Body:
        return self._body

    def header(self) -> Header:
        return self._header

    def set_header(self, **kwargs):
        """
        something useful for content parser and connect manage
        - headers
            -- content_length：body length
        """
        # TODO: extend header fields
        cl = kwargs.get("content_length")
        if cl is not None:
            self._header.content_length = cl

    def set_body(self, body: ByteString):
        self._body = body

    def append_body(self, tail: ByteString):
        self._body += tail


class DefaultReader(BaseReader):

    def __init__(self, compress: BaseCompress = default_compress):
        self._buffer_size = 256
        self.compress = compress

    def __call__(self, conn) -> Tuple[ByteString, BaseRequest]:
        print(f"read from {conn}")  # change to log
        data = b''
        request = DefaultRequest()
        while True:
            try:
                d = conn.recv(4)
                if not d:
                    break
                cl = struct.unpack('I', d)[0]
                request.set_header(content_length=cl)
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
            except BlockingIOError:  # no-blocking socket called blocking function
                pass
            except ConnectionResetError:  # register connect was closed by peer
                pass
        if data:
            print(data)
            if self.compress is not None:
                data = self.compress.decompress(data)
            request.set_body(data)
        # body default is None
        return request.body(), request


class DefaultWriter(BaseWriter):

    def __init__(self, compress: BaseCompress = default_compress):
        self.compress = compress

    def __call__(self, conn, handler: BaseHandler, request: BaseRequest):
        resp = handler(request)
        send_body = resp.body()
        if self.compress is not None:
            pass
            send_body = self.compress.compress(send_body)  # type: bytes  # noqa
        send_header = struct.pack("I", len(send_body))
        conn.send(send_header + send_body)


class DefaultHandler(BaseHandler):

    def __call__(self, request: BaseRequest) -> BaseResponse:
        resp = DefaultResponse()
        # TODO: handler data and response
        resp.set_body(request.body())
        return resp
