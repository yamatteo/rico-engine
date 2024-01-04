from typing import Literal, Optional, overload

from attr import Factory, asdict, define

from .holders import Holder

from .constants import *
from .utils import WorkplaceData, bin_extend, bin_mod


@define
class Town(Holder):
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

    tiles: dict[Tile, WorkplaceData] = Factory(
        lambda: {tile: WorkplaceData(0, 0) for tile in TILES}
    )

    buildings: dict[Building, WorkplaceData] = Factory(
        lambda: {b: WorkplaceData(0, 0) for b in BUILDINGS}
    )

    def active_quarries(self) -> int:
        return self.tiles["quarry_tile"].worked

    # def active_tiles(self, type: Tile) -> int:
    #     return self.worked_tiles[TILES.index(type)]

    def active_workers(
        self, subclass: Literal["coffee", "tobacco", "sugar", "indigo"]
    ) -> int:
        if subclass == "coffee":
            space = BUILD_INFO["coffee_roaster"]["space"]
            workers = self.buildings["coffee_roaster"].worked
            return min(space, workers)
        if subclass == "indigo":
            space_i = BUILD_INFO["small_indigo_plant"]["space"]
            workers_i = self.buildings["small_indigo_plant"].worked
            space_j = BUILD_INFO["indigo_plant"]["space"]
            workers_j = self.buildings["indigo_plant"].worked
            return min(space_i, workers_i) + min(space_j, workers_j)
        if subclass == "sugar":
            space_i = BUILD_INFO["sugar_mill"]["space"]
            workers_i = self.buildings["sugar_mill"].worked
            space_j = BUILD_INFO["small_sugar_mill"]["space"]
            workers_j = self.buildings["small_sugar_mill"].worked
            return min(space_i, workers_i) + min(space_j, workers_j)
        if subclass == "tobacco":
            space = BUILD_INFO["tobacco_storage"]["space"]
            workers = self.buildings["tobacco_storage"].worked
            return min(space, workers)

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

    def count_free_build_space(self) -> int:
        total = 12
        for building, data in self.buildings.items():
            if data.placed > 0:
                total -= 2 if building in LARGE_BUILDINGS else 1
        return total

    def count_tiles(self):
        return sum(placed for placed, _ in self.tiles.values())

    def count_total_jobs(self) -> int:
        return sum(data.placed for data in self.tiles.values()) + sum(
            BUILD_INFO[building]["space"]
            for building, data in self.buildings.items()
            if data.placed > 0
        )

    def count_total_people(self) -> int:
        return (
            self.people
            + sum(data.worked for data in self.tiles.values())
            + sum(data.worked for data in self.buildings.values())
        )

    def count_vacant_building_jobs(self) -> int:
        total = 0
        for building, data in self.buildings.items():
            if data.placed > 0:
                space = BUILD_INFO[building]["space"]
                people = data.worked
                total += max(0, space - people)
        return total

    # def count_workers(self, build_type: Building) -> int:
    #     i = BUILDINGS.index(build_type)
    #     return max(0, self.buildings_mixed[i])

    # def copy(self):
    #     return deepcopy(self)

    def privilege(self, subclass: Building) -> bool:
        space = BUILD_INFO[subclass]["space"]
        workers = self.buildings[subclass].worked
        return workers >= space

    @overload
    def production(self) -> dict[Good, int]:
        ...

    @overload
    def production(self, good: Good) -> int:
        ...

    def production(self, good: Optional[Good] = None):
        if not good:
            return {_good: self.production(_good) for _good in GOODS}
        tile: Tile = f"{good}_tile"  # type: ignore
        raw_production = self.tiles[tile].worked
        if good == "corn":
            return raw_production
        active_workers = self.active_workers(good)
        return min(raw_production, active_workers)

    @overload
    def list_buildings(self) -> list[Building]:
        ...

    @overload
    def list_buildings(self, attr: str) -> list[int]:
        ...

    def list_buildings(self, attr="types"):
        if attr == "people":
            return [info.worked for info in self.buildings.values() if info.placed > 0]
        types: list[Building] = [b for b, info in self.buildings.items() if info.placed > 0]
        if attr == "types":
            return types
        elif attr == "space":
            return [BUILD_INFO[t]["space"] for t in types]
        elif attr == "tier":
            return [BUILD_INFO[t]["tier"] for t in types]

    def list_tiles(self) -> list[Tile]:
        l = []
        for tile, data in self.tiles.items():
            l.extend([tile] * data.placed)
        return l

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

    def tally_details(self) -> tuple[int, ...]:
        """The value of the town as calculated after game over and its precursors."""

        # Points from shipping goods
        points = self.points

        # Points from buildings
        buildings = sum(
            BUILD_INFO[building]["tier"]
            for building, data in self.buildings.items()
            if data.placed > 0
        )

        # Points from large buildings
        city_hall = 0
        if self.privilege("city_hall"):
            city_hall += len(
                [
                    building
                    for building, data in self.buildings.items()
                    if building in NONPROD_BUILDINGS and data.placed > 0
                ]
            )

        custom_house = 0
        if self.privilege("custom_house"):
            custom_house += self.points // 4

        fortress = 0
        if self.privilege("fortress"):
            fortress += self.count_total_people() // 3

        guild_hall = 0
        if self.privilege("guild_hall"):
            for building, data in self.buildings.items():
                if data.placed == 0:
                    continue
                if building in ["small_indigo_plant", "small_sugar_mill"]:
                    guild_hall += 1
                if building in [
                    "coffee_roaster",
                    "indigo_plant",
                    "sugar_mill",
                    "tobacco_storage",
                ]:
                    guild_hall += 2

        residence = 0
        if self.privilege("residence"):
            occupied_tiles = sum(data.worked for data in self.tiles.values())
            residence += max(4, occupied_tiles - 5)

        value = (
            points
            + buildings
            + guild_hall
            + residence
            + fortress
            + custom_house
            + city_hall
        )
        return (
            value,
            points,
            buildings,
            city_hall,
            custom_house,
            fortress,
            guild_hall,
            residence,
        )
