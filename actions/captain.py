from typing import Literal, Optional, Sequence

from attr import define

from .. import GOODS, Board, Good, ShipData
from .base import Action
from .refuse import RefuseAction


@define
class CaptainAction(Action):
    selected_ship: Optional[int] = None
    selected_good: Optional[Good] = None
    type: Literal["captain"] = "captain"
    priority: int = 5

    def __str__(self):
        return f"{self.name}.captain({self.selected_good} in {self.selected_ship})"

    def possibilities(self, board: Board, **kwargs) -> Sequence[Action]:
        town = board.towns[self.name]
        actions = [] + [RefuseAction(name=town.name)]
        for selected_good in GOODS:
            if not town.has(selected_good):
                continue
            if town.privilege("wharf") and not town.spent_wharf:
                actions.append(
                    CaptainAction(
                        name=town.name, selected_good=selected_good, selected_ship=11
                    )
                )
            for ship_size in board.goods_fleet:
                if board.ship_accept(ship_size=ship_size, good=selected_good):
                    actions.append(
                        CaptainAction(
                            name=town.name,
                            selected_good=selected_good,
                            selected_ship=ship_size,
                        )
                    )

        return actions

    def react(action, board: Board) -> tuple[Board, Sequence[Action]]:
        town = board.towns[action.name]
        ship_size = action.selected_ship
        good = action.selected_good
        assert ship_size is not None
        assert good is not None

        # Want to use wharf
        if ship_size == 11:
            assert town.privilege("wharf") and not town.spent_wharf, "Player does not have a free wharf."

            town.spent_wharf = True
            amount = town.count(good)
            town.give(amount, good, to=board)
            points = amount
            if town.privilege("harbor"):
                points += 1
            if town.role == "captain" and not town.spent_captain:
                points += 1
                town.spent_captain = True
            board.give_or_make(points, "points", to=town)

        else:
            assert board.ship_accept(ship_size=ship_size, good=good), f"Ship {ship_size} cannot accept {good}."

            size, type, amount = board.goods_fleet[ship_size]
            given_amount = min(size - amount, town.count(good))
            board.goods_fleet[ship_size] = ShipData(size, type, amount+town.pop(good, given_amount))

            points = given_amount
            if town.privilege("harbor"):
                points += 1
            if town.role == "captain" and not town.spent_captain:
                points += 1
                town.spent_captain = True
            board.give_or_make(points, "points", to=town)

        extra = []
        if sum(town.count(g) for g in GOODS) > 0:
            extra = [CaptainAction(name=action.name)]

        return board, extra
