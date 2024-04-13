from typing import Literal

## Types

ActionType = Literal[
    "builder",
    "captain",
    "craftsman",
    "governor",
    "mayor",
    "role",
    "settler",
    "storage",
    "tidyup",
    "trader",
]

Building = Literal[
    "city_hall",
    "coffee_roaster",
    "construction_hut",
    "custom_house",
    "factory",
    "fortress",
    "guild_hall",
    "hacienda",
    "harbor",
    "hospice",
    "indigo_plant",
    "large_market",
    "large_warehouse",
    "office",
    "residence",
    "small_indigo_plant",
    "small_market",
    "small_sugar_mill",
    "small_warehouse",
    "sugar_mill",
    "tobacco_storage",
    "university",
    "wharf",
]

Good = Literal[
    "corn",
    "indigo",
    "sugar",
    "tobacco",
    "coffee",
]

LargeBuilding = Literal[
    "city_hall",
    "custom_house",
    "fortress",
    "guild_hall",
    "residence",
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
    "coffee_roaster",
    "construction_hut",
    "custom_house",
    "factory",
    "fortress",
    "guild_hall",
    "hacienda",
    "harbor",
    "hospice",
    "indigo_plant",
    "large_market",
    "large_warehouse",
    "office",
    "residence",
    "small_indigo_plant",
    "small_market",
    "small_sugar_mill",
    "small_warehouse",
    "sugar_mill",
    "tobacco_storage",
    "university",
    "wharf",
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


## Constants

ACTIONS: tuple[ActionType, ...] = (
    "builder",
    "captain",
    "craftsman",
    "governor",
    "mayor",
    "role",
    "settler",
    "storage",
    "tidyup",
    "trader",
)

GOODS: tuple[Good, ...] = (
    "corn",
    "indigo",
    "sugar",
    "tobacco",
    "coffee",
)

LARGE_BUILDINGS: tuple[LargeBuilding, ...] = (
    "city_hall",
    "custom_house",
    "fortress",
    "guild_hall",
    "residence",
)

PROD_BUILDINGS: tuple[ProdBuilding, ...] = (
    "coffee_roaster",
    "indigo_plant",
    "small_indigo_plant",
    "small_sugar_mill",
    "sugar_mill",
    "tobacco_storage",
)

ROLES: tuple[Role, ...] = (
    "builder",
    "captain",
    "craftsman",
    "mayor",
    "settler",
    "trader",
    "prospector",
    "second_prospector",
)

SMALL_BUILDINGS: tuple[SmallBuilding, ...] = (
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
)

TILES: tuple[Tile, ...] = (
    "coffee_tile",
    "corn_tile",
    "indigo_tile",
    "quarry_tile",
    "sugar_tile",
    "tobacco_tile",
)

COUNTABLES = GOODS + ("money", "people", "points")

NONPROD_BUILDINGS: tuple[Building, ...] = SMALL_BUILDINGS + LARGE_BUILDINGS

BUILDINGS: tuple[Building, ...] = PROD_BUILDINGS + NONPROD_BUILDINGS


## Additional information

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
