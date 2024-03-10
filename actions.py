from typing import Literal, Optional, Sequence, Union
from attr import define, asdict
from itertools import product, combinations
from copy import deepcopy
import random

from .boards import Board
from . import (
    ActionType,
    ROLES,
    GOODS,
    Good,
    BUILDINGS,
    LARGE_BUILDINGS,
    BUILD_INFO,
    Building,
    TILES,
    Tile,
    Role,
    Town,
    ShipData,
    WorkplaceData,
)

PeopleHolder = Union[Literal["home"], Tile, Building]
PeopleAssignment = tuple[PeopleHolder, int]
PeopleDistribution = list[PeopleAssignment]

class GameOver(Exception):
    pass

@define
class Action:
    name: str
    type: ActionType
    priority: int

    def possibilities(self, board: Board, **kwargs) -> Sequence["Action"]:
        raise NotImplementedError

    def react(self, board: Board) -> tuple[Board, Sequence["Action"]]:
        raise NotImplementedError

    def responds_to(self, other: "Action") -> bool:
        exact_type = self.type == other.type
        exact_name = self.name == other.name
        complete = all(value is not None for value in asdict(self).values())
        return exact_type and exact_name and complete

@define
class GovernorAction(Action):
    type: Literal["governor"] = "governor"
    priority: int = 0

    def __str__(self):
        return f"{self.name}.governor()"

    def possibilities(self, board: Board, **kwargs):
        return [self]

    def react(action, board: Board) -> tuple[Board, Sequence[Action]]:
        board.set_governor(action.name)
        extra = [RoleAction(name=name) for name in board.round_from(action.name)]
        extra += [GovernorAction(name=board.next_to(action.name))]
        
        if not board.is_end_of_round():
            # Game just started, nothing else to do
            return board, extra

        # Increase money bonus of unchosen roles
        if board.money >= 3:
            board.reset_roles()
        else:
            return board, [ TerminateAction(name=action.name, reason="Not enough money for roles.")]

        return board, extra

@define
class RoleAction(Action):
    role: Optional[Role] = None
    type: Literal["role"] = "role"
    priority: int = 2

    def __str__(self):
        return f"{self.name}.take_role({self.role})"

    def possibilities(self, board: Board, **kwargs) -> list["RoleAction"]:
        return [
            RoleAction(name=self.name, role=role)
            for role, data in board.roles.items()
            if data.available 
        ]

    def react(action, board: Board) -> tuple[Board, Sequence[Action]]:
        town = board.towns[action.name]
        role = action.role

        assert role is not None, f"{action!r} is not complete."
        assert town.role is None, f"Player {town.name} already has role ({town.role})."
        

        board.give_role(role, to=town)
        extra: Sequence[Action] = []

        if role == "settler":
            extra = [
                SettlerAction(name=name) for name in board.round_from(town.name)
            ] + [TidyUpAction(name=action.name)]
        elif role == "mayor":
            if board.has("people"):
                board.give(1, "people", to=town)
            while board.people_ship:
                for some_town in board.town_round_from(town.name):
                    if board.people_ship > 0:
                        board.people_ship -= 1
                        some_town.people += 1
                    else:
                        break

            extra.extend(MayorAction(name=name) for name in board.round_from(town.name))
            extra.append(TidyUpAction(name=action.name))

        elif role == "builder":
            extra = [BuilderAction(name=name) for name in board.round_from(town.name)]
        elif role == "craftsman":
            for some_town in board.town_round_from(town.name):
                for good, amount in some_town.production().items():
                    possible_amount = min(amount, board.count(good))
                    board.give(possible_amount, good, to=some_town)
            extra = [CraftsmanAction(name=town.name)]
        elif role == "trader":
            extra = [
                TraderAction(name=name) for name in board.round_from(town.name)
            ] + [TidyUpAction(name=action.name)]
        elif role == "captain":
            extra = (
                [CaptainAction(name=name) for name in board.round_from(town.name)]
                + [StorageAction(name=name) for name in board.round_from(town.name)]
                + [TidyUpAction(name=action.name)]
            )
        elif role in ["prospector1", "prospector2"]:
            if board.has("money"):
                board.give(1, "money", to=town)
                extra = []
            if board.count("money") <= 0:
                extra = [TerminateAction(name=action.name, reason="No more money.")]

        return board, extra

@define
class TerminateAction(Action):
    reason: str
    type: Literal["terminate"] = "terminate"
    priority: int = 1
    
    def possibilities(self, board: Board, **kwargs) -> list[Action]:
        return [self]

    def react(action, board: Board):
        raise GameOver(action.reason)

@define
class BuilderAction(Action):
    building_type: Optional[Building] = None
    extra_person: bool = False
    type: Literal["builder"] = "builder"
    priority: int = 5

    def __str__(self):
        return f"{self.name}.build({self.building_type}{' with worker' if self.extra_person else ''})"

    def possibilities(self, board: Board, **kwargs) -> Sequence[Action]:
        town = board.towns[self.name]

        extra_person_possibilities = (
            [False, True] if town.privilege("hospice") and board.people > 0 else [False]
        )

        type_possibilities: list[Building] = []
        for type in BUILDINGS:
            tier = BUILD_INFO[type]["tier"]
            cost = BUILD_INFO[type]["cost"]
            free_space = town.count_free_build_space()
            required_space = 2 if type in LARGE_BUILDINGS else 1
            quarries_discount = min(tier, town.active_quarries())
            builder_discount = 1 if town.role == "builder" else 0
            price = max(0, cost - quarries_discount - builder_discount)
            if (
                board.unbuilt[type] > 0  # A building of this type is available
                and town.buildings[type].placed == 0  # Town doesn't have it
                and town.money >= price  # Town has enough money
                and free_space >= required_space  # Town has enough space
            ):
                type_possibilities.append(type)

        return [RefuseAction(name=town.name)] + [
            BuilderAction(name=town.name, building_type=type, extra_person=extra)
            for (type, extra) in product(type_possibilities, extra_person_possibilities)
        ]

    def react(action, board: Board):
        town = board.towns[action.name]
        assert action.building_type is not None, f"Action {action} is not complete."

        board.give_building(action.building_type, to=town)
        if action.extra_person:
            assert (
                town.privilege("hospice") and board.people > 0
            ), "Can't ask for extra worker"
            board.people -= 1
            town.buildings[action.building_type] = WorkplaceData(1, 1)

        extra = []
        # Stop for building space
        if town.count_free_build_space() == 0:
            extra.append(
                TerminateAction(
                    name=action.name, reason="Game over: no more real estate."
                )
            )

        return board, extra

@define
class RefuseAction(Action):
    type: Literal["refuse"] = "refuse"
    priority: int = 4

    def __str__(self):
        return f"{self.name}.refuse()"

    def possibilities(self, board: Board, **kwargs):
        return [self]

    def react(action, board: Board) -> tuple[Board, list[Action]]:
        return board, []
    
    def responds_to(self, other: "Action") -> bool:
        exact_name = self.name == other.name
        refusal_type = other.type in [
            "builder", 
            "captain", 
            "craftsman",  
            "settler", 
            "storage", 
            "trader", 
        ]
        return refusal_type and exact_name

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

            amount = board.goods_fleet[ship_size].amount
            given_amount = min(ship_size - amount, town.count(good))

            board.load_cargo(town.pop(good, given_amount), good, ship_size)

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
            actions = [
StorageAction(
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

@define
class TidyUpAction(Action):
    type: Literal["tidyup"] = "tidyup"
    priority: int = 3

    def __str__(self):
        return f"{self.name}.tidyup()"

    def react(action, board: Board) -> tuple[Board, Sequence[Action]]:
        extra = []

        # Check if enough tiles are revealed
        if len(board.exposed_tiles) <= len(board.towns):
            board.expose_tiles()
        
        # Check ships and market
        board.empty_ships_and_market()
        
        # Eventually refill people_ship
        if board.people_ship <= 0:
            total_jobs = sum(town.count_vacant_building_jobs() for town in board.towns.values())
            total_jobs = max(total_jobs, len(board.towns))  # At least one per player
            if board.count("people") >= total_jobs:
                board.people_ship = board.pop("people", total_jobs)
            else:
                extra.append(TerminateAction(name=action.name, reason="No more people."))
        
        # Check that there are points left
        if board.points <= 0:
            extra.append(TerminateAction(name=action.name, reason="No more points."))

        return board, extra
    
    def possibilities(self, board: Board, **kwargs) -> Sequence[Action]:
        return [self]

@define
class CraftsmanAction(Action):
    selected_good: Optional[Good] = None
    type: Literal["craftsman"] = "craftsman"
    priority: int = 5

    def __str__(self):
        return f"{self.name}.supercraft({self.selected_good})"

    def react(action, board: Board) -> tuple[Board, list[Action]]:
        good = action.selected_good
        town = board.towns[action.name]
        assert good is not None, "Action is not complete."
        assert town.production(good) > 0, f"Craftsman get one extra good of something he produces, not {good}."

        assert board.has(good), f"There is no {good} left in the game."
        board.give(1, good, to=town)
        return board, []

    def possibilities(self, board: Board, **kwargs) -> Sequence[Action]:
        town = board.towns[self.name]
        actions = list()
        for selected_good in GOODS:
            if town.production(selected_good) > 0 and board.has(selected_good):
                actions.append(
                    CraftsmanAction(name=town.name, selected_good=selected_good)
                )
        actions.append(RefuseAction(name=town.name))
        return actions

@define
class MayorAction(Action):
    people_distribution: Optional[PeopleDistribution] = None
    type: Literal["mayor"] = "mayor"
    priority: int = 5

    def __str__(self):
        if not self.people_distribution:
            return f"{self.name}.mayor(?)"
        occupations = str(", ").join(
            f"{holder}={amount}" for holder, amount in self.people_distribution
        )
        return f"{self.name}.mayor({occupations})"

    def react(action, board: Board) -> tuple[Board, list[Action]]:
        town = board.towns[action.name]
        assert action.people_distribution is not None, "Action is incomplete."

        updated_town = deepcopy(town)
        (first_holder, people_at_home), *assignments = action.people_distribution
        holders = updated_town.list_tiles() + updated_town.list_buildings()
        assert first_holder == "home", "Need to now how many worker stay home."
        assert len(assignments) == len(
            holders
        ), f"There should be assignments for every tile/building exactly. Got {assignments} for {holders}"

        updated_town.people = people_at_home
        worked_tiles = {tile: 0 for tile in TILES}
        worked_buildings = {building: 0 for building in updated_town.buildings}
        for (holder_type, amount), holder in zip(assignments, holders):
            assert holder_type == holder, f"Wrong assignment: {holder_type} to {holder}"

            if holder in BUILDINGS:
                worked_buildings[holder] += amount
            elif holder in TILES:
                worked_tiles[holder] += amount

        for tile, (placed, _) in town.tiles.items():
            updated_town.tiles[tile] = WorkplaceData(placed, worked_tiles[tile])

        for building, (placed, _) in town.buildings.items():
            updated_town.buildings[building] = WorkplaceData(
                placed, worked_buildings[building]
            )

        assert (
            updated_town.count_total_people() == town.count_total_people()
        ), "Wrong total of people."

        board.towns[town.name] = updated_town
        return board, []

    def possibilities(self, board: Board, cap=None, **kwargs) -> list["MayorAction"]:
        town = board.towns[self.name]
        people, space = town.count_total_people(), town.count_total_jobs()
        holders = [
            "home",
            *town.list_tiles(),
            *town.list_buildings(),
        ]

        if people >= space:
            dist = tuple(
                people - space
                if key == "home"
                else (1 if key in TILES else BUILD_INFO[key]["space"])  # type: ignore
                for key in holders
            )
            return [
                MayorAction(
                    name=town.name,
                    people_distribution=list(zip(holders, dist)),  # type: ignore
                )
            ]
        else:
            dist = tuple(
                0 if key == "home" else (1 if key in TILES else BUILD_INFO[key]["space"])  # type: ignore
                for key in holders
            )
            distributions = {dist}
            total_people_in_new_dist = sum(dist)
        while total_people_in_new_dist > people:
            new_distributions = set()
            for dist in distributions:
                for i, value in enumerate(dist):
                    if value > 0:
                        next_dist = list(dist)
                        next_dist[i] = value - 1
                        new_distributions.add(tuple(next_dist))

            total_people_in_new_dist -= 1
            if cap and cap < len(new_distributions):
                distributions = random.sample(new_distributions, cap)
            else:
                distributions = new_distributions

        return [
            MayorAction(name=town.name, people_distribution=list(zip(holders, dist)))  # type: ignore
            for dist in distributions
        ]

@define
class SettlerAction(Action):
    tile: Optional[Tile] = None
    down_tile: bool = False
    extra_person: bool = False
    type: Literal["settler"] = "settler"
    priority: int = 5

    def __str__(self):
        return f"{self.name}.settler({self.tile}{' +downtile' if self.down_tile else ''}{' +worker' if self.extra_person else ''})"

    def react(action, board: Board) -> tuple[Board, list[Action]]:
        town: Town = board.towns[action.name]
        
        assert action.tile is not None, "Action is not complete"
        assert not action.down_tile or town.privilege("hacienda"), "Can't take down tile without occupied hacienda."
        assert not action.extra_person or town.privilege("hospice"), "Can't take extra person without occupied hospice."
        assert action.tile != "quarry" or town.role == "settler" or town.privilege("construction_hut"), "Only the settler can pick a quarry"
        assert sum(data.placed for data in town.tiles.values()) < 12, "At most 12 tile per player."

        tile_index = TILES.index(action.tile)
        board.give_tile(to=town, type=action.tile)
        if action.extra_person and board.has("people"):
            board.pop("people", 1)
            placed, worked = town.tiles[action.tile]
            town.tiles[action.tile] = WorkplaceData(placed, worked+1)
        if action.down_tile and board.unsettled_tiles and sum(data.placed for data in town.tiles.values()) < 12:
            board.give_facedown_tile(to=town)
        
        return board, []

    def possibilities(self, board: Board, **kwargs) -> Sequence[Action]:
        town = board.towns[self.name]
        actions = []
        if sum(data.placed for data in town.tiles.values()) < 12:
            tiletypes = set(board.exposed_tiles)
            if board.unsettled_quarries and (town.role == "settler" or town.privilege("construction_hut")):
                tiletypes.add("quarry_tile")
            for tile_type in tiletypes:
                actions.append(SettlerAction(name=town.name, tile=tile_type))
                if town.privilege("hacienda") and town.privilege("hospice"):
                    actions.append(SettlerAction(name=town.name, tile=tile_type, down_tile=True, extra_person=True))
                if town.privilege("hacienda"):
                    actions.append(SettlerAction(name=town.name, tile=tile_type, down_tile=True))
                if town.privilege("hospice"):
                    actions.append(SettlerAction(name=town.name, tile=tile_type, extra_person=True))
            

        return [RefuseAction(name=town.name)] + actions

@define
class TraderAction(Action):
    selected_good: Optional[Good] = None
    type: Literal["trader"] = "trader"
    priority: int = 5
    
    def __str__(self):
        return f"{self.name}.trade({self.selected_good})"

    def react(action, board: Board) -> tuple[Board, list[Action]]:
        good = action.selected_good
        town = board.towns[action.name]
        assert good is not None, "Action is not complete"
        assert sum(board.market.count(g) for g in GOODS) < 4, "There is no more space in the market."
        assert board.market.count(good) == 0 or town.privilege("office"), f"There already is {good} in the market."
        price = dict(corn=0, indigo=1, sugar=2, tobacco=3, coffee=4)[good]
        price += 1 if town.role == "trader" else 0
        price += 1 if town.privilege("small_market") else 0
        price += 2 if town.privilege("large_market") else 0
        affordable_price = min(price, board.count("money"))
        town.pop(good, 1)
        board.market.append(good)
        board.give(affordable_price, "money", to=town)
        return board, []

    def possibilities(self, board: Board, **kwargs) -> Sequence[Action]:
        town = board.towns[self.name]
        actions = [RefuseAction(name=town.name)]
        if sum(board.market.count(g) for g in GOODS) >= 4:
            return actions
        for selected_good in [good for good in GOODS if town.has(good)]:
            if board.market.count(selected_good) == 0 or town.privilege("office"): # type: ignore
                actions = actions + [
                    TraderAction(
                        name=town.name, selected_good=selected_good # type: ignore
                    )
                ]
        return actions