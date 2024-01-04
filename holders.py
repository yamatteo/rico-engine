from typing import Literal, Union, overload

from attr import define


class Holder:
    def add(self, attr: str, value: int):
        setattr(self, attr, getattr(self, attr) + value)

    def count(self, attr: str) -> int:
        return getattr(self, attr, 0)

    @overload
    def has(self, attr: str) -> bool:
        ...

    @overload
    def has(self, amount: int, attr: str) -> bool:
        ...

    def has(self, *args): # type: ignore
        if len(args) == 2:
           amount: int = args[0]
           type: str = args[1]
        else:
            amount: int = 1
            type: str = args[0]
        return getattr(self, type, 0) >= amount

    def give(self, amount: Union[int, Literal["all"]], attr: str, *, to: "Holder"):
        if amount == "all":
            amount = self.count(attr)
        assert hasattr(to, attr), f"Object {to} can't accept {attr}."
        assert self.count(attr) >= amount, f"Not enough {attr} in {self}."
        self.set(attr, self.count(attr) - amount)
        to.set(attr, to.count(attr) + amount)

    def give_or_make(self, amount: Union[int, Literal["all"]], attr: str, *, to: "Holder"):
        if amount == "all":
            amount = self.count(attr)
        assert hasattr(to, attr), f"Object {to} can't accept {attr}."
        self.set(attr, max(0, self.count(attr) - amount))
        to.set(attr, to.count(attr) + amount)
    
    def pop(self, attr: str, value: int) -> int:
        assert self.has(value, attr), f"Object {self} don't have {value} {attr}."
        self.add(attr, -value)
        return value

    def set(self, attr: str, amount: int):
        setattr(self, attr, amount)
