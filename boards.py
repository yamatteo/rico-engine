import itertools
import random
from copy import deepcopy
from typing import Iterator, Sequence, Union

from attr import define

from .holders import Holder

from .constants import *
from .towns import Town
from .utils import RoleData, ShipData, WorkplaceData, bin_extend, bin_mod


@define
class Board(Holder):
    towns: dict[str, Town]

    money: int
    people: int
    points: int
    coffee: int
    corn: int
    indigo: int
    sugar: int
    tobacco: int

    roles: dict[Role, RoleData]

    goods_fleet: dict[int, ShipData]
    market: list[Good]
    people_ship: int
    unbuilt: dict[Building, int]
    unsettled_quarries: int
    exposed_tiles: list[Tile]
    unsettled_tiles: list[Tile]

    def __getitem__(self, name: str):
        return self.towns[name]

    @classmethod
    def new(cls, names: Sequence[str], shuffle_tiles=True):
        assert 3 <= len(names) <= 5, "Players must be between 3 and 5."

        game_data = {}
        game_data["towns"] = {name: Town(name=name) for name in names}

        game_data["money"] = 54
        game_data["people"] = 20 * len(names) - 5
        game_data["points"] = 122
        game_data["coffee"] = 9
        game_data["corn"] = 10
        game_data["indigo"] = 11
        game_data["sugar"] = 11
        game_data["tobacco"] = 9

        game_data["people_ship"] = len(names)
        game_data["market"] = []
        game_data["goods_fleet"] = {
            n: ShipData(n, None, 0) for n in range(len(names) + 1, len(names) + 4)
        }

        # Generate role cards
        game_data["roles"] = {
            r: RoleData(i < len(names) + 3, 0)
            for i in range(8)
            for i, r in enumerate(ROLES)
        }

        # Generate tiles
        game_data["unsettled_quarries"] = 8
        game_data["unsettled_tiles"] = list()
        game_data["exposed_tiles"] = list(
            sum(([tile] * amount for tile, amount in TILE_INFO.items()), start=[])
        )
        if shuffle_tiles:
            random.shuffle(game_data["exposed_tiles"])

        # Generate buildings
        game_data["unbuilt"] = {
            building: info["initial"] for building, info in BUILD_INFO.items()
        }

        self = cls(**game_data)

        # Distribute money
        amount = len(names) - 1
        for town in self.towns.values():
            self.money -= amount
            town.money += amount

        # Distribute tiles
        num_indigo = 2 if len(names) < 5 else 3
        for i, player_name in enumerate(names):
            player = self.towns[player_name]
            self.give_tile(
                to=player, type="indigo_tile" if i < num_indigo else "corn_tile"
            )
        self.expose_tiles()

        # # Take first action (governor assignment)
        # self.take_action()
        return self

    def asdict(self):
        d = dict()

        for role, data in self.roles.items():
            d[f"{role} is available"] = data.available

            bin_extend(d, f"{role} money", data.money, sup=7)

        bin_extend(d, "money", self.money, sup=60)
        bin_extend(d, "people", self.people, sup=100)
        bin_extend(d, "points", self.points, sup=122)

        for good in GOODS:
            bin_extend(d, good, getattr(self, good), sup=12)

        bin_extend(d, f"covered tiles", len(self.unsettled_tiles), sup=63)
        bin_extend(d, f"quarries", self.unsettled_quarries, sup=7)

        for type in TILE_INFO:
            bin_extend(d, type, self.exposed_tiles.count(type), sup=6)

        bin_extend(d, "people in ship", self.people_ship, sup=15)

        for ship in self.goods_fleet.values():
            bin_extend(d, f"ship({ship.size}) space", ship.size - ship.amount, sup=7)
            for good in GOODS:
                d[f"ship({ship.size}) has {good}"] = int(ship.type == good)

        bin_extend(d, f"market space", 4 - len(self.market), sup=4)
        for good in GOODS:
            d[f"market has {good}"] = int(good in self.market)

        for building, info in BUILD_INFO.items():
            bin_extend(d, building, self.unbuilt[building], sup=info["initial"])

        return d

    def empty_ships_and_market(self):
        for size, data in self.goods_fleet.items():
            _, type, amount = data
            if amount >= size:
                self.goods_fleet[size] = ShipData(size, None, 0)
                self.add(type, amount)
        market_total = len(self.market)
        if market_total >= 4:
            for type in self.market:
                self.add(type, 1)
            self.market = []

    def expose_tiles(self):
        tiles = self.unsettled_tiles + self.exposed_tiles

        self.exposed_tiles = tiles[: len(self.towns) + 1]
        self.unsettled_tiles = tiles[len(self.towns) + 1 :]

    def give_building(self, building_type: Building, *, to: Union[Town, str]):
        if isinstance(to, str):
            town = self.towns[to]
        else:
            town = to

        buildinfo = BUILD_INFO[building_type]
        tier = buildinfo["tier"]
        cost = buildinfo["cost"]
        quarries_discount = min(tier, town.active_quarries())
        builder_discount = 1 if town.role == "builder" else 0
        price = max(0, cost - quarries_discount - builder_discount)
        assert town.money >= price, f"Player does not have enough money."
        assert (
            self.unbuilt[building_type] > 0
        ), f"There are no more {building_type} to sell."
        assert town.count_free_build_space() >= (
            2 if tier == 4 else 1
        ), f"Town of {town.name} does not have space for {building_type}"
        assert (
            town.buildings[building_type].placed == 0
        ), f"Town of {town.name} already has a {building_type}"

        self.unbuilt[building_type] -= 1
        town.buildings[building_type] = WorkplaceData(1, 0)
        town.money -= price
        self.money += price

    def give_facedown_tile(self, to: Town):
        assert len(self.unsettled_tiles) > 0, "No more covert tiles."
        assert to.count_tiles() < 12, "No more space to place a tile."

        type = self.unsettled_tiles.pop(0)
        placed, worked = to.tiles[type]
        to.tiles[type] = WorkplaceData(placed + 1, worked)

    def give_tile(self, type: Tile, *, to: Town):
        if type == "quarry_tile":
            self.give_quarry(to)
        elif type == "down":
            self.give_facedown_tile(to)
        else:
            assert type in self.exposed_tiles, f"No {type} exposed."
            assert to.count_tiles() < 12, "No more space to place a quarry."

            self.exposed_tiles.remove(type)
            placed, worked = to.tiles[type]
            to.tiles[type] = WorkplaceData(placed + 1, worked)

    def give_quarry(self, to: Town):
        assert self.unsettled_quarries > 0, "No more quarry to give."
        assert to.count_tiles() < 12, "No more space to place a quarry."
        self.unsettled_quarries -= 1
        placed, worked = to.tiles["quarry_tile"]
        to.tiles["quarry_tile"] = WorkplaceData(placed + 1, worked)

    def give_role(self, role: Role, *, to: Union[str, Town]):
        if isinstance(to, str):
            town = self.towns[to]
        else:
            town = to

        assert town.role is None, f"Player {to} already as role {town.role}."
        assert role in ROLES, f"Role {role} is not available."

        # i = ROLES.index(role)
        assert role in self.roles, f"Role {role} is not available."
        # available_roles = [role for role, amount in zip(ROLES, self.roles) if amount > -1]
        # role_type = role.type if isinstance(role, Role) else role
        # enforce(role_type in available_roles, f"Role {role_type} is not available.")
        # i = available_roles.index(role_type)

        # town.add("money", self.roles[i])
        town.role = role
        town.money += self.roles[role].money
        # self.roles[i] = -1
        self.roles[role] = RoleData(False, 0)
        # self.roles[i].give("all", "money", to=town)
        # town.role = self.roles.pop(i)

    def is_end_of_round(self):
        return all((town.role is not None) for town in self.towns.values())

    def load_cargo(self, amount: int, type: Good, size: int):
        _, _, prev_amount = self.goods_fleet[size]
        self.goods_fleet[size] = ShipData(size, type, prev_amount + amount)

    def next_to(self, name: str) -> str:
        cycle = itertools.cycle(self.towns)
        for owner in cycle:
            if name == owner:
                break
        return next(cycle)

    def reset_roles(self):
        for role, data in self.roles.items():
            if data.available:
                assert self.money > 0, "Error! No more money for roles!"
                self.money -= 1
                self.roles[role] = RoleData(True, data.money + 1)
            else:
                self.roles[role] = RoleData(True, 0)

        # Set town roles to None
        for town in self.towns.values():
            town.role = None
            town.spent_wharf = False
            town.spent_captain = False

    def round_from(self, wrt: str) -> Iterator[str]:
        cycle = itertools.cycle(self.towns)

        curr_player_name = next(cycle)
        while curr_player_name != wrt:
            curr_player_name = next(cycle)

        for _ in range(len(self.towns)):
            yield curr_player_name
            curr_player_name = next(cycle)

    def town_round_from(self, wrt: str) -> Iterator[Town]:
        for town_name in self.round_from(wrt):
            yield self.towns[town_name]

    def set_governor(self, name: str):
        for owner, town in self.towns.items():
            town.gov = owner == name

    def ship_accept(self, ship_size, good) -> bool:
        for size, data in self.goods_fleet.items():
            if size != ship_size and data.type == good:
                return False
        if self.goods_fleet[ship_size].amount == 0:
            return True
        elif self.goods_fleet[ship_size].type != good:
            return False
        else:
            return self.goods_fleet[ship_size].amount < ship_size
