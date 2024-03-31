from collections import namedtuple
import math
from typing import Generic, List as TypingList, Optional, TypeVar

from attr import define

from .constants import Good, PeopleHolder


def bin_mod(n: int, log2=0) -> int:
    return (n // (2**log2)) % 2


def bin_extend(d: dict, label: str, value: int, sup: int):
    log2 = 0
    num_bits = math.ceil(math.log(sup + 1, 2))
    sup = 2**num_bits - 1
    while log2 < num_bits:
        d[f"{label} %% {2**log2}"] = bin_mod(min(sup, value), log2)
        log2 += 1


@define
class ShipData:
    size: int
    type: Optional[Good]
    amount: int


@define
class RoleData:
    available: int
    money: int


@define
class WorkplaceData:
    placed: int
    worked: int
    
    def __iter__(self):
        yield self.placed
        yield self.worked

@define
class PeopleAssignment:
    holder: PeopleHolder
    amount: int
