from .. import Board, Town


def straight_town_estimator(town: Town) -> int:
    return town.tally_details()[0]


def straight_board_estimator(board: Board, wrt: str) -> int:
    return straight_town_estimator(board.towns[wrt])