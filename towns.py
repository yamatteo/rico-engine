from typing import Literal, Optional, overload

from attr import Factory, asdict, define

from .constants import *
from .utils import WorkplaceData, bin_extend, bin_mod


@define
class Town:
    name: str

    gov: bool = False
    spent_captain: bool = False
    spent_wharf: bool = False

    role: Optional[Role] = None

    money: int = 0
    people: int = 0  # Not counting workers of tiles and buildings.
    points: int = 0
    coffee: int = 0
    corn: int = 0
    indigo: int = 0
    sugar: int = 0
    tobacco: int = 0
    
    tiles: dict[Tile, WorkplaceData] = Factory(lambda: {tile: WorkplaceData(0, 0) for tile in TILES})
    
    buildings: dict[Building, WorkplaceData] = Factory(lambda: {b: WorkplaceData(0, 0) for b in BUILDINGS})

    # def active_quarries(self):
    #     return self.worked_tiles[TILES.index("quarry")]

    # def active_tiles(self, type: Tile) -> int:
    #     return self.worked_tiles[TILES.index(type)]

    # def active_workers(
    #     self, subclass: Literal["coffee", "tobacco", "sugar", "indigo"]
    # ) -> int:
    #     if subclass == "coffee":
    #         i = BUILDINGS.index("coffee_roaster")
    #         space = BUILDINFO["coffee_roaster"]["space"]
    #         workers = max(0, self.buildings_mixed[i])
    #         return min(space, workers)
    #     if subclass == "indigo":
    #         i = BUILDINGS.index("small_indigo_plant")
    #         space_i = BUILDINFO["small_indigo_plant"]["space"]
    #         workers_i = max(0, self.buildings_mixed[i])
    #         j = BUILDINGS.index("indigo_plant")
    #         space_j = BUILDINFO["indigo_plant"]["space"]
    #         workers_j = max(0, self.buildings_mixed[j])
    #         return min(space_i, workers_i) + min(space_j, workers_j)
    #     if subclass == "sugar":
    #         i = BUILDINGS.index("sugar_mill")
    #         space_i = BUILDINFO["sugar_mill"]["space"]
    #         workers_i = max(0, self.buildings_mixed[i])
    #         j = BUILDINGS.index("small_sugar_mill")
    #         space_j = BUILDINFO["small_sugar_mill"]["space"]
    #         workers_j = max(0, self.buildings_mixed[j])
    #         return min(space_i, workers_i) + min(space_j, workers_j)
    #     if subclass == "tobacco":
    #         i = BUILDINGS.index("tobacco_storage")
    #         space = BUILDINFO["tobacco_storage"]["space"]
    #         workers = max(0, self.buildings_mixed[i])
    #         return min(space, workers)
    
    def asdict(self) -> dict:
        d = dict()

        d["is governor"] = int(self.gov)
        d["spent captain"] = int(self.spent_captain)
        d["spent wharf"] = int(self.spent_wharf)

        bin_extend(d, "money", self.money, sup=15)
        bin_extend(d, "people", self.people, sup=7)
        bin_extend(d, "points", self.points, sup=100)

        for good in GOODS:
            bin_extend(d, good, getattr(self, good), sup=12)

        for r in ROLES:
            d[r] = int(self.role == r)

        for tile, data in self.tiles.items():
            bin_extend(d, f"placed {tile}", data.placed, sup=12)
            bin_extend(d, f"worked {tile}", data.placed, sup=12)
        
        for building in PROD_BUILDINGS:
            data = self.buildings[building]
            d[f"{building} placed"] = data.placed
            d[f"{building} worked %% 1"] = bin_mod(data.worked, 0)
            d[f"{building} worked %% 2"] = bin_mod(data.worked, 1)
        
        for building in NONPROD_BUILDINGS:
            data = self.buildings[building]
            d[f"{building} placed"] = data.placed
            d[f"{building} worked"] = data.worked

        return d
    
    # def as_tuple(self) -> tuple[int, ...]:
    #     """Town as a tuple of ints without loss of information."""
    #     self_as_list = []
    #     self_as_list_names = []

    #     # Some information is already a counting integer, or a boolean integer
    #     self_as_list_names += [
    #                 "gov",
    #                 "spent_captain",
    #                 "spent_wharf",
    #                 "coffee",
    #                 "corn",
    #                 "indigo",
    #                 "money",
    #                 "people",
    #                 "points",
    #                 "sugar",
    #                 "tobacco",
    #             ]
        
    #     self_as_list += [
    #             int(getattr(self, name))
    #             for name in self_as_list_names
    #     ]

    #     # One hot encoding of the role, no role goes to (0, 0, 0, ...)
    #     self_as_list_names += list(ROLES)
    #     self_as_list += [int(self.role == r) for r in ROLES]

    #     for tile, data in self.tiles.items():
    #         self_as_list_names += [f"placed {tile} > {n}" for n in range(12)]
    #         self_as_list += [int(data.placed > n) for n in range(12)]
    #         self_as_list_names += [f"worked {tile} > {n}" for n in range(12)]
    #         self_as_list += [int(data.worked > n) for n in range(12)]
        
    #     for building in PROD_BUILDINGS:
    #         data = self.buildings[building]
    #         self_as_list_names += [f"{building} placed"] + [f"{building} worked > {n}" for n in range(3)]
    #         self_as_list += [data.placed] + [int(data.worked > n) for n in range(3)]
        
    #     for building in NONPROD_BUILDINGS:
    #         data = self.buildings[building]
    #         self_as_list_names += [f"{building} placed", f"{building} worked"]
    #         self_as_list += [data.placed, data.worked]

    #     return tuple(self_as_list_names), tuple(self_as_list)

    # def count_farmers(self, tile_type: Tile) -> int:
    #     return self.worked_tiles[TILES.index(tile_type)]

    # def count_free_build_space(self) -> int:
    #     total = 12
    #     for tier in self.list_buildings("tier"):
    #         total -= 2 if tier == 4 else 1
    #     return total

    def count_tiles(self):
        return sum(placed for placed, _ in self.tiles.values())

    # def count_total_jobs(self) -> int:
    #     return sum(self.placed_tiles) + sum(self.list_buildings("space"))

    # def count_total_people(self) -> int:
    #     return (
    #         self.count("people")
    #         + sum(self.worked_tiles)
    #         + sum(self.list_buildings("people"))
    #     )

    # def count_vacant_building_jobs(self) -> int:
    #     total = 0
    #     for space, people in zip(
    #         self.list_buildings("space"), self.list_buildings("people")
    #     ):
    #         total += max(0, space - people)
    #     return total

    # def count_workers(self, build_type: Building) -> int:
    #     i = BUILDINGS.index(build_type)
    #     return max(0, self.buildings_mixed[i])

    # def copy(self):
    #     return deepcopy(self)

    # def privilege(self, subclass: Building) -> bool:
    #     space = BUILDINFO[subclass]["space"]
    #     workers = self.count_workers(subclass)
    #     return workers >= space

    # @overload
    # def production(self) -> dict[GoodType, int]:
    #     ...

    # @overload
    # def production(self, good: GoodType) -> int:
    #     ...

    # def production(self, good: Optional[GoodType] = None):
    #     if not good:
    #         return {_good: self.production(_good) for _good in GOODS}
    #     raw_production = self.active_tiles(good)
    #     if good == "corn":
    #         return raw_production
    #     active_workers = self.active_workers(good)
    #     return min(raw_production, active_workers)

    # @overload
    # def list_buildings(self) -> list[Building]:
    #     ...

    # @overload
    # def list_buildings(self, attr: str) -> list[int]:
    #     ...

    # def list_buildings(self, attr="types") -> list[Building]:
    #     if attr == "people":
    #         return [info for info in self.buildings_mixed if info > -1]
    #     types = [b for b, info in zip(BUILDINGS, self.buildings_mixed) if info > -1]
    #     if attr == "types":
    #         return types
    #     elif attr == "space":
    #         return [BUILDINFO[t]["space"] for t in types]
    #     elif attr == "tier":
    #         return [BUILDINFO[t]["tier"] for t in types]

    # def list_tiles(self) -> list[Tile]:
    #     l = []
    #     for tile, placed in zip(TILES, self.placed_tiles):
    #         l.extend([tile] * placed)
    #     return l

    # @property
    # def role(self) -> Optional[Role]:
    #     if self.role_index == -1:
    #         return None
    #     return ROLES[self.role_index]

    # @role.setter
    # def role(self, role: Optional[Role]):
    #     if role is None:
    #         i = -1
    #     else:
    #         i = ROLES.index(role)
    #     self.role_index = i
    
    # def tally_details(self) -> tuple[int, ...]:
    #     """The value of the town as calculated after game over and its precursors."""

    #     # Points from shipping goods
    #     points = self.count("points")

    #     # Points from buildings
    #     buildings = sum(self.list_buildings("tier"))

    #     # Points from large buildings
    #     city_hall = 0
    #     if self.privilege("city_hall"):
    #         city_hall += len(
    #             [
    #                 building
    #                 for building in self.list_buildings()
    #                 if building not in PROD_BUILDINGS
    #             ]
    #         )

    #     custom_house = 0
    #     if self.privilege("custom_house"):
    #         custom_house += self.count("points") // 4

    #     fortress = 0
    #     if self.privilege("fortress"):
    #         fortress += self.count_total_people() // 3

    #     guild_hall = 0
    #     if self.privilege("guild_hall"):
    #         for building in self.list_buildings():
    #             if building in ["small_indigo_plant", "small_sugar_mill"]:
    #                 guild_hall += 1
    #             if building in [
    #                 "coffee_roaster",
    #                 "indigo_plant",
    #                 "sugar_mill",
    #                 "tobacco_storage",
    #             ]:
    #                 guild_hall += 2

    #     residence = 0
    #     if self.privilege("residence"):
    #         occupied_tiles = sum(self.worked_tiles)
    #         residence += max(4, occupied_tiles - 5)

    #     value = points + buildings + guild_hall + residence + fortress + custom_house + city_hall
    #     return value, points, buildings, city_hall, custom_house, fortress, guild_hall, residence

    # def tally(self):
    #     points = self.count("points")

    #     # Buildings
    #     points += sum(self.list_buildings("tier"))

    #     # Large buildings
    #     if self.privilege("guild_hall"):
    #         for building in self.list_buildings():
    #             if building in ["small_indigo_plant", "small_sugar_mill"]:
    #                 points += 1
    #             if building in [
    #                 "coffee_roaster",
    #                 "indigo_plant",
    #                 "sugar_mill",
    #                 "tobacco_storage",
    #             ]:
    #                 points += 2
    #     if self.privilege("residence"):
    #         occupied_tiles = sum(self.worked_tiles)
    #         points += max(4, occupied_tiles - 5)
    #     if self.privilege("fortress"):
    #         points += self.count_total_people() // 3
    #     if self.privilege("custom_house"):
    #         points += self.count("points") // 4
    #     if self.privilege("city_hall"):
    #         points += len(
    #             [
    #                 building
    #                 for building in self.list_buildings()
    #                 if building not in PROD_BUILDINGS
    #             ]
    #         )

    #     return points
