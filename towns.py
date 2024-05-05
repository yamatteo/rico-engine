from typing import Optional, overload

from attr import Factory, define

from .constants import *
from .holders import Holder
from .utils import WorkplaceData, bin_extend, bin_mod


@define
class Town(Holder):
    name: str

    gov: bool = False
    spent_role: bool = True
    # spent_captain: bool = False
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

    # def asdict_binary(self) -> dict:
    #     data = dict()

    #     data["is governor"] = int(self.gov)
    #     data["spent captain"] = int(self.spent_captain)
    #     data["spent wharf"] = int(self.spent_wharf)

    #     bin_extend(data, "money", self.money, sup=15)
    #     bin_extend(data, "people", self.people, sup=7)
    #     bin_extend(data, "points", self.points, sup=100)

    #     for good in GOODS:
    #         bin_extend(data, good, getattr(self, good), sup=12)

    #     for r in ROLES:
    #         data[r] = int(self.role == r)

    #     for tile, data in self.tiles.items():
    #         bin_extend(data, f"placed {tile}", data.placed, sup=12)
    #         bin_extend(data, f"worked {tile}", data.placed, sup=12)

    #     for building in PROD_BUILDINGS:
    #         data = self.buildings[building]
    #         data[f"{building} placed"] = data.placed
    #         data[f"{building} worked %% 1"] = bin_mod(data.worked, 0)
    #         data[f"{building} worked %% 2"] = bin_mod(data.worked, 1)

    #     for building in NONPROD_BUILDINGS:
    #         data = self.buildings[building]
    #         data[f"{building} placed"] = data.placed
    #         data[f"{building} worked"] = data.worked

    #     return data

    def asdict_integers(self) -> dict[str, int]:
        data = dict()

        data["is_governor"] = int(self.gov)
        data["spent_role"] = int(self.spent_role)
        data["spent_wharf"] = int(self.spent_wharf)

        data["money"] = self.money
        data["points"] = self.points
        data["people"] = self.people
        data["role"] = 1 + ROLES.index(self.role) if self.role else 0
        for good in GOODS:
            data[good] = self.count(good)

        for tile, info in self.tiles.items():
            data[f"placed_{tile}"] = info.placed
            data[f"worked_{tile}"] = info.worked

        for building, info in self.buildings.items():
            data[f"placed_{building}"] = info.placed
            data[f"worked_{building}"] = info.worked

        return data

    def asdict_strings(self) -> dict[str, int]:
        data = dict()

        data["is_governor"] = str(int(self.gov))
        data["spent_role"] = str(int(self.spent_role))
        data["spent_wharf"] = str(int(self.spent_wharf))

        data["money"] = f"{self.money:02}"
        data["points"] = f"{self.points:02}"
        data["people"] = str(self.people)
        data["role"] = {
            None: "0",
            "builder": "B",
            "captain": "C",
            "craftsman": "F",
            "mayor": "M",
            "settler": "S",
            "trader": "T",
            "prospector": "P",
            "second_prospector": "P",
        }[self.role]
        for good in GOODS:
            data[good] = str(self.count(good))

        for tile, info in self.tiles.items():
            data[f"placed_{tile}"] = f"{info.placed:X}"
            data[f"worked_{tile}"] = f"{info.worked:X}"

        for building, info in self.buildings.items():
            data[f"placed_{building}"] = str(info.placed)
            data[f"worked_{building}"] = str(info.worked)

        return data

    def count_active_quarries(self) -> int:
        return self.tiles["quarry_tile"].worked

    def count_active_workers(self, good: Good) -> int:
        production_buildings = dict(
            corn=[],
            indigo=["small_indigo_plant", "indigo_plant"],
            sugar=["small_sugar_mill", "sugar_mill"],
            tobacco=["tobacco_storage"],
            coffee=["coffee_roaster"],
        )[good]
        return sum(self.buildings[building].worked for building in production_buildings)

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

    def privilege(self, building: Building) -> bool:
        space = BUILD_INFO[building]["space"]
        workers = self.buildings[building].worked
        return workers >= space

    def placed_buildings(self) -> list[Building]:
        return [b for b, info in self.buildings.items() if info.placed > 0]

    def placed_tiles(self) -> list[Tile]:
        return [tile for tile, data in self.tiles.items() if data.placed > 0]

    @overload
    def production(self) -> dict[Good, int]: ...

    @overload
    def production(self, good: Good) -> int: ...

    def production(self, good: Optional[Good] = None):
        if not good:
            return {_good: self.production(_good) for _good in GOODS}
        tile: Tile = f"{good}_tile"  # type: ignore
        raw_production = self.tiles[tile].worked
        if good == "corn":
            return raw_production
        active_workers = self.count_active_workers(good)
        return min(raw_production, active_workers)

    def tally(self) -> int:
        """The value (victory points) of the town as calculated at game over."""
        return sum(self.tally_details())

    def tally_details(self) -> tuple[int, ...]:
        """The precursors of value of the town as calculated after game over."""

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

        return (
            points,
            buildings,
            city_hall,
            custom_house,
            fortress,
            guild_hall,
            residence,
        )
