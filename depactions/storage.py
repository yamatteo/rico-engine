from itertools import combinations
from typing import Literal, Optional, Sequence

from attr import define

from .. import GOODS, Good, Board

from .base import Action
from .refuse import RefuseAction


@define
class StorageAction(Action):
    selected_good: Optional[Good] = None
    small_warehouse_good: Optional[Good] = None
    large_warehouse_first_good: Optional[Good] = None
    large_warehouse_second_good: Optional[Good] = None
    type: Literal["storage"] = "storage"
    priority: int = 4

    def __str__(self):
        stored = [self.selected_good, self.small_warehouse_good, self.large_warehouse_first_good, self.large_warehouse_second_good]
        stored = [ g for g in stored if g in GOODS ]
        return f"{self.name}.store({str(', ').join(stored)})"

    def react(action, board: Board) -> tuple[Board, list[Action]]:
        town = board.towns[action.name]

        for good in GOODS:
            if good in [
                action.small_warehouse_good,
                action.large_warehouse_first_good,
                action.large_warehouse_second_good,
            ]:
                continue
            elif good == action.selected_good:
                town.give(max(0, town.count(good) - 1), good, to=board)
            else:
                town.give("all", good, to=board)
        return board, []
    
    def responds_to(self, other: "Action") -> bool:
        exact_type = self.type == other.type
        exact_name = self.name == other.name
        return exact_type and exact_name

    def possibilities_with_three_warehouses(self, board: Board) -> list["StorageAction"]:
        town = board.towns[self.name]
        actions = []
        excess_goods: list[Good] = [good for good in GOODS if town.has(good)]
        if len(excess_goods) > 3:
            for stored_goods in combinations(excess_goods, 4):
                actions.append(
                        StorageAction(
                            name=town.name,
                            selected_good=stored_goods[0],
                            small_warehouse_good=stored_goods[1],
                            large_warehouse_first_good=stored_goods[2],
                            large_warehouse_second_good=stored_goods[3],
                        )
                    )
        elif len(excess_goods) == 3:
            actions = [StorageAction(
                            name=town.name,
                            small_warehouse_good=excess_goods[0],
                            large_warehouse_first_good=excess_goods[1],
                            large_warehouse_second_good=excess_goods[2],
                        )]
        elif len(excess_goods) == 2:
            actions = [StorageAction(
                            name=town.name,
                            large_warehouse_first_good=excess_goods[0],
                            large_warehouse_second_good=excess_goods[1],
                        )]
        elif len(excess_goods) == 1:
            actions = [StorageAction(
                            name=town.name,
                            small_warehouse_good=excess_goods[0],
                        )]
        return actions
    

    def possibilities_with_two_warehouses(self, board: Board) -> list["StorageAction"]:
        town = board.towns[self.name]
        actions = []
        excess_goods: list[Good] = [good for good in GOODS if town.has(good)]
        if len(excess_goods) > 2:
            for stored_goods in combinations(excess_goods, 3):
                actions.append(
                    StorageAction(
                        name=town.name,
                        selected_good=stored_goods[0],
                        large_warehouse_first_good=stored_goods[1],
                        large_warehouse_second_good=stored_goods[2],
                    )
                )
        elif len(excess_goods) == 2:
            actions = [StorageAction(
                            name=town.name,
                            large_warehouse_first_good=excess_goods[0],
                            large_warehouse_second_good=excess_goods[1],
                        )]
        elif len(excess_goods) == 1:
            actions = [StorageAction(
                            name=town.name,
                            large_warehouse_first_good=excess_goods[0],
                        )]
        return actions

    def possibilities_with_one_warehouses(self, board: Board) -> list["StorageAction"]:
        town = board.towns[self.name]
        actions = []
        excess_goods: list[Good] = [good for good in GOODS if town.has(good)]
        if len(excess_goods) > 1:
            for stored_goods in combinations(excess_goods, 2):
                actions.append(
                    StorageAction(
                        name=town.name,
                        selected_good=stored_goods[0],
                        small_warehouse_good=stored_goods[1],
                    )
                )
        elif len(excess_goods) == 1:
            actions = [StorageAction(
                            name=town.name,
                            small_warehouse_good=excess_goods[0],
                        )]
        return actions

    def possibilities_with_no_warehouse(self, board: Board) -> list["StorageAction"]:
        town = board.towns[self.name]
        actions = []
        excess_goods: list[Good] = [good for good in GOODS if town.has(good)]
        for selected_good in excess_goods:
            actions.append(
                StorageAction(
                    name=town.name,
                    selected_good=selected_good,
                )
            )
        return actions

    def possibilities(self, board: Board, **kwargs) -> Sequence[Action]:
        town = board.towns[self.name]
        if town.privilege("large_warehouse") and town.privilege("small_warehouse"):
            actions = self.possibilities_with_three_warehouses(board)
        elif town.privilege("large_warehouse"):
            actions = self.possibilities_with_two_warehouses(board)
        elif town.privilege("small_warehouse"):
            actions = self.possibilities_with_one_warehouses(board)
        else:
            actions = self.possibilities_with_no_warehouse(board)
        return [RefuseAction(name=town.name)] + actions
