import itertools
import random
from copy import deepcopy
from typing import Iterator, Union

from attr import define

from .constants import *
from .utils import WorkplaceData as TownData
from .towns import Town
from .utils import RoleData, ShipData, bin_extend, bin_mod


@define
class Board:
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
    def new(cls, names: list[str]):
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
        game_data["goods_fleet"] = {n: ShipData(n, None, 0) for n in range(len(names) + 1, len(names) + 4)}

        # Generate role cards
        game_data["roles"] = {r:RoleData(i < len(names) + 3, 0) for i in range(8) for i, r in enumerate(ROLES)}

        # Generate tiles
        game_data["unsettled_quarries"] = 8
        game_data["unsettled_tiles"] = list()
        game_data["exposed_tiles"] = list(sum(([tile]*amount for tile, amount in TILE_INFO.items()), start=[]))
        random.shuffle(game_data["exposed_tiles"])

        # Generate buildings
        game_data["unbuilt"] = {
            building: info["initial"]
            for building, info in BUILD_INFO.items()
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
            self.give_tile(to=player, type="indigo_tile" if i < num_indigo else "corn_tile")
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
            bin_extend(d, f"ship({ship.size}) space", ship.size-ship.amount, sup=7)
            for good in GOODS:
                d[f"ship({ship.size}) has {good}"] = int(ship.type == good)

        bin_extend(d, f"market space", 4 - len(self.market), sup=4)
        for good in GOODS:
            d[f"market has {good}"] = int(good in self.market)
        
        for building, info in BUILD_INFO.items():
            bin_extend(d, building, self.unbuilt[building], sup=info['initial'])
        
        return d
    
    def astuple(self, wrt: str):
        output_tuple = tuple(self.asdict().values())
        for town in self.town_round_from(wrt):
            output_tuple += tuple(town.asdict().values())
        return output_tuple


    # def as_tuples(self, wrt: str) -> tuple[tuple[int, ...], ...]:
    #     tiles = (len(self.unsettled_tiles), self.unsettled_quarries) + tuple(
    #         self.exposed_tiles.count(tile_type) for tile_type in GOODS
    #     )
    #     roles_money = tuple(self.roles)
    #     ships = [self.people_ship.people]
    #     for ship in self.goods_fleet.values():
    #         ships.extend([ship.size] + [ship.count(kind) for kind in GOODS])
    #     ships = tuple(ships)
    #     market = tuple(self.market.count(kind) for kind in GOODS)
    #     buildings = tuple(self.unbuilt.count(kind) for kind in BUILDINGS)
        
    #     board = direct + roles_money + tiles + ships + market + buildings
    #     towns = tuple(town.as_tuple() for town in self.town_round_from(wrt))

    #     return board, *towns

    # def copy(self):
    #     return deepcopy(self)
    
    # def count_unsettled_tiles(self):
    #     return sum(self.unsettled_tiles.values())

    # def empty_ships_and_market(self):
    #     for size, ship in self.goods_fleet.items():
    #         what, amount = next(ship.items(), (None, 0))
    #         if amount >= size:
    #             ship.give(amount, what, to=self)
    #     market_total = sum(amount for type, amount in self.market.items())
    #     if market_total >= 4:
    #         for type, amount in self.market.items():
    #             self.market.give(amount, type, to=self)

    def expose_tiles(self):
        tiles = self.unsettled_tiles + self.exposed_tiles
        
        self.exposed_tiles = tiles[: len(self.towns) + 1]
        self.unsettled_tiles = tiles[len(self.towns) + 1 :]
        
    # def give_building(self, building_type: Building, *, to: Town):
    #     if isinstance(to, str):
    #         town = self.towns[to]
    #     else:
    #         town = to

    #     buildinfo = BUILDINFO[building_type]
    #     tier = buildinfo["tier"]
    #     cost = buildinfo["cost"]
    #     quarries_discount = min(tier, town.active_quarries())
    #     builder_discount = 1 if town.role == "builder" else 0
    #     price = max(0, cost - quarries_discount - builder_discount)
    #     enforce(town.has(price, "money"), f"Player does not have enough money.")
    #     enforce(
    #         [type for type in self.unbuilt if type == building_type],
    #         f"There are no more {building_type} to sell.",
    #     )
    #     enforce(
    #         town.count_free_build_space() >= (2 if tier == 4 else 1),
    #         f"Town of {town.name} does not have space for {building_type}",
    #     )
    #     enforce(
    #         building_type not in town.list_buildings(),
    #         f"Town of {town.name} already has a {building_type}",
    #     )

    #     i, type = next(
    #         (i, type) for i, type in enumerate(self.unbuilt) if type == building_type
    #     )
    #     self.unbuilt.pop(i)
    #     town.buildings_mixed[BUILDINGS.index(type)] = 0
    #     town.give(price, "money", to=self)

    def give_facedown_tile(self, to: Town):
        assert len(self.unsettled_tiles) > 0, "No more covert tiles."
        assert to.count_tiles() < 12, "No more space to place a tile."

        type = self.unsettled_tiles.pop(0)
        placed, worked = to.tiles[type] 
        to.tiles[type] = TownData(placed+1, worked)

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
            to.tiles[type] = TownData(placed+1, worked)

    def give_quarry(self, to: Town):
        assert self.unsettled_quarries > 0, "No more quarry to give."
        assert to.count_tiles() < 12, "No more space to place a quarry."
        self.unsettled_quarries -= 1
        placed, worked = to.tiles["quarry_tile"] 
        to.tiles["quarry_tile"] = TownData(placed+1, worked)

    # def give_role(self, role: Role, *, to: Union[str, Town]):
    #     if isinstance(to, str):
    #         town = self.towns[to]
    #     else:
    #         town = to
    #     enforce(town.role is None, f"Player {to} already as role {town.role}.")

    #     enforce(role in ROLES, f"Role {role} is not available.")
    #     i = ROLES.index(role)
    #     enforce(self.roles[i] > -1, f"Role {role} is not available.")
    #     # available_roles = [role for role, amount in zip(ROLES, self.roles) if amount > -1]
    #     # role_type = role.type if isinstance(role, Role) else role
    #     # enforce(role_type in available_roles, f"Role {role_type} is not available.")
    #     # i = available_roles.index(role_type)

    #     town.add("money", self.roles[i])
    #     self.roles[i] = -1
    #     town.role = role
    #     # self.roles[i].give("all", "money", to=town)
    #     # town.role = self.roles.pop(i)

    # def is_end_of_round(self):
    #     return all((town.role_index != -1) for town in self.towns.values())

    # def next_to(self, wrt: str) -> str:
    #     cycle = itertools.cycle(self.towns)
    #     for owner in cycle:
    #         if wrt == owner:
    #             break
    #     return next(cycle)

    # def pay_roles(self):
    #     # assert It's a bug!
    #     for i in range(len(self.towns) + 3):
    #         if self.roles[i] == -1:
    #             self.roles[i] = 0
    #         else:
    #             self.roles[i] += self.pop("money", 1)
    #     # for card in self.roles:
    #     #     self.give(1, "money", to=card)

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

    # def set_governor(self, wrt: str):
    #     for owner, town in self.towns.items():
    #         town.gov = int(owner == wrt)
