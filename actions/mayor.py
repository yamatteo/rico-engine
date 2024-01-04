from copy import deepcopy
import random
from typing import Literal, Optional, Union

from attr import define


from .. import BUILD_INFO, BUILDINGS, TILES, Board, Building, Tile, WorkplaceData
from .base import Action

PeopleHolder = Union[Literal["home"], Tile, Building]
PeopleAssignment = tuple[PeopleHolder, int]
PeopleDistribution = list[PeopleAssignment]


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
