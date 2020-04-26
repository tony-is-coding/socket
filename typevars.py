from typing import Union, Set, Tuple, List, Dict, AnyStr
from dataclasses import dataclass
from typing import ByteString

PyObject = Union[Set, Tuple, List, Dict, AnyStr, int]
Body = ByteString


@dataclass(eq=False, repr=False)
class Header:
    content_length: int
