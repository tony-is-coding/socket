#############################################
#                                           #
#                                           #
#   this module just use for inheritance    #
#                                           #
#                                           #
#############################################

from abc import ABCMeta, abstractmethod

from typevars import Header, Body


class BaseWriter(metaclass=ABCMeta):

    @abstractmethod
    def __call__(self, *args, **kwargs):
        ...


class BaseReader(metaclass=ABCMeta):

    @abstractmethod
    def __call__(self, *args, **kwargs):
        ...


class BaseRequest(metaclass=ABCMeta):

    @abstractmethod
    def body(self) -> Body:
        ...

    @abstractmethod
    def header(self) -> Header:
        ...


class BaseResponse(metaclass=ABCMeta):
    @abstractmethod
    def body(self) -> Body:
        ...

    @abstractmethod
    def header(self) -> Header:
        ...


class BaseHandler(metaclass=ABCMeta):

    @abstractmethod
    def __call__(self, *args, **kwargs) -> BaseResponse:  # TODO: return a structure response
        ...
