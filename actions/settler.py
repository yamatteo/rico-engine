from typing import Literal, Optional, Sequence

from attr import define

from .. import TILES, Board, Tile, Town, WorkplaceData
from .base import Action
from .refuse import RefuseAction
from .tidyup import TidyUpAction


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
