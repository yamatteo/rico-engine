from typing import Literal, Union, get_args

ActionType = Literal[
    "builder",
    "captain",
    "craftsman",
    "governor",
    "mayor",
    # "refuse",
    "role",
    "settler",
    "storage",
    # "terminate",
    "tidyup",
    "trader",
]

Good = Literal[
    "coffee",
    "corn",
    "indigo",
    "sugar",
    "tobacco",
]
LargeBuilding = Literal[
    "city_hall",
    "custom_house",
    "fortress",
    "guild_hall",
    "residence",
]
ProdBuilding = Literal[
    "coffee_roaster",
    "indigo_plant",
    "small_indigo_plant",
    "small_sugar_mill",
    "sugar_mill",
    "tobacco_storage",
]
Role = Literal[
    "builder",
    "captain",
    "craftsman",
    "mayor",
    "settler",
    "trader",
    "prospector",
    "second_prospector",
]
SmallBuilding = Literal[
    "construction_hut",
    "factory",
    "hacienda",
    "harbor",
    "hospice",
    "large_market",
    "large_warehouse",
    "office",
    "small_market",
    "small_warehouse",
    "university",
    "wharf",
]
Tile = Literal[
    "coffee_tile",
    "corn_tile",
    "indigo_tile",
    "quarry_tile",
    "sugar_tile",
    "tobacco_tile",
]
PeopleHolder = Literal[
    "home",
    "coffee_tile",
    "corn_tile",
    "indigo_tile",
    "quarry_tile",
    "sugar_tile",
    "tobacco_tile",
    "city_hall",
    "custom_house",
    "fortress",
    "guild_hall",
    "residence",
    "coffee_roaster",
    "indigo_plant",
    "small_indigo_plant",
    "small_sugar_mill",
    "sugar_mill",
    "tobacco_storage",
    "construction_hut",
    "factory",
    "hacienda",
    "harbor",
    "hospice",
    "large_market",
    "large_warehouse",
    "office",
    "small_market",
    "small_warehouse",
    "university",
    "wharf",
]

# Building = Union[ProdBuilding, SmallBuilding, LargeBuilding]
Building = Literal[
    "city_hall",
    "custom_house",
    "fortress",
    "guild_hall",
    "residence",
    "coffee_roaster",
    "indigo_plant",
    "small_indigo_plant",
    "small_sugar_mill",
    "sugar_mill",
    "tobacco_storage",
    "construction_hut",
    "factory",
    "hacienda",
    "harbor",
    "hospice",
    "large_market",
    "large_warehouse",
    "office",
    "small_market",
    "small_warehouse",
    "university",
    "wharf",
]

ACTIONS: tuple[ActionType, ...] = (
    "builder",
    "captain",
    "craftsman",
    "governor",
    "mayor",
    # "refuse",
    "role",
    "settler",
    "storage",
    # "terminate",
    "tidyup",
    "trader",
)
GOODS: tuple[Good, ...] = get_args(Good)
LARGE_BUILDINGS: tuple[LargeBuilding, ...] = get_args(LargeBuilding)
PROD_BUILDINGS: tuple[ProdBuilding, ...] = get_args(ProdBuilding)
ROLES: tuple[Role, ...] = get_args(Role)
SMALL_BUILDINGS: tuple[SmallBuilding, ...] = get_args(SmallBuilding)
TILES: tuple[Tile, ...] = get_args(Tile)

COUNTABLES = GOODS + ("money", "people", "points")
NONPROD_BUILDINGS: tuple[Building, ...] = SMALL_BUILDINGS + LARGE_BUILDINGS
BUILDINGS: tuple[Building, ...] = PROD_BUILDINGS + NONPROD_BUILDINGS

BUILD_INFO: dict[Building, dict[str, int]] = {
    "city_hall": {"tier": 4, "cost": 10, "space": 1, "initial": 1},
    "coffee_roaster": {"tier": 3, "cost": 6, "space": 2, "initial": 3},
    "construction_hut": {"tier": 1, "cost": 2, "space": 1, "initial": 2},
    "custom_house": {"tier": 4, "cost": 10, "space": 1, "initial": 1},
    "factory": {"tier": 3, "cost": 7, "space": 1, "initial": 2},
    "fortress": {"tier": 4, "cost": 10, "space": 1, "initial": 1},
    "guild_hall": {"tier": 4, "cost": 10, "space": 1, "initial": 1},
    "hacienda": {"tier": 1, "cost": 2, "space": 1, "initial": 2},
    "harbor": {"tier": 3, "cost": 8, "space": 1, "initial": 2},
    "hospice": {"tier": 2, "cost": 4, "space": 1, "initial": 2},
    "indigo_plant": {"tier": 2, "cost": 3, "space": 3, "initial": 3},
    "large_market": {"tier": 2, "cost": 5, "space": 1, "initial": 2},
    "large_warehouse": {"tier": 2, "cost": 6, "space": 1, "initial": 2},
    "office": {"tier": 2, "cost": 5, "space": 1, "initial": 2},
    "residence": {"tier": 4, "cost": 10, "space": 1, "initial": 1},
    "small_indigo_plant": {"tier": 1, "cost": 1, "space": 1, "initial": 4},
    "small_market": {"tier": 1, "cost": 1, "space": 1, "initial": 2},
    "small_sugar_mill": {"tier": 1, "cost": 2, "space": 1, "initial": 4},
    "small_warehouse": {"tier": 1, "cost": 3, "space": 1, "initial": 2},
    "sugar_mill": {"tier": 2, "cost": 4, "space": 3, "initial": 3},
    "tobacco_storage": {"tier": 3, "cost": 5, "space": 3, "initial": 3},
    "university": {"tier": 3, "cost": 8, "space": 1, "initial": 2},
    "wharf": {"tier": 3, "cost": 9, "space": 1, "initial": 2},
}

TILE_INFO: dict[Tile, int] = {
    "coffee_tile": 8,
    "corn_tile": 10,
    "indigo_tile": 12,
    "sugar_tile": 11,
    "tobacco_tile": 9,
}
