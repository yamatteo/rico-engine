from collections import namedtuple
import math
from typing import Generic, List as TypingList, TypeVar


def bin_mod(n: int, log2=0) -> int:
    return (n // (2**log2)) % 2

def bin_extend(d: dict, label: str, value: int, sup: int):
    log2 = 0
    num_bits = math.ceil(math.log(sup+1, 2))
    sup = 2**num_bits - 1
    while log2 < num_bits:
        d[f"{label} %% {2**log2}"] = bin_mod(min(sup, value), log2)
        log2 += 1


ShipData = namedtuple("ShipData", ["size", "type", "amount"])
RoleData = namedtuple("RoleData", ["available", "money"])
WorkplaceData = namedtuple("WorkplaceData", ["placed", "worked"])