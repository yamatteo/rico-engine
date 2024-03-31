import unittest


from .actions import *
from .boards import Board
from .constants import BUILDINGS, GOODS, ROLES
from .game import Game
from .towns import Town
from .utils import WorkplaceData


class TestFixedGame4(unittest.TestCase):
    def setUp(self):
        self.game = Game.start(["Aaron", "Bard", "Carl", "Dave"], shuffle=False)
    
    def test_setup(self):
        game, board = self.game, self.game.board
        Aa, Ba, Ca, Da = board.towns.values()
        assert Aa.name == "Aa"
        assert game.play_order == ["Aa", "Ba", "Ca", "Da"]
        self.assertEqual(list(game.current_round()), list(game.board.towns.values()))
    
    def test_points_are_given_even_when_there_is_no_points_left(self):
        game, board = self.game, self.game.board
        Aa, Ba, Ca, Da = board.towns.values()
        Aa.corn = 3
        board.points = 1
        game.take_action(GovernorAction("Aa"))
        game.take_action(RoleAction("Aa", role="captain"))
        game.take_action(CaptainAction("Aa", selected_ship=5, selected_good="corn"))
        assert board.points == 0
        assert Aa.points == 4  # Three from corn, one for being captain
    
    def test_serialization(self):
        data = self.game.dumps()
        self.assertIsInstance(data, str)
        reconstructed_game = Game.loads(data)
        self.assertEqual(self.game, reconstructed_game)

    def test_builder_role(self):
        self.game.take_action(GovernorAction("Aa"))
        self.game.take_action(RoleAction("Aa", role="builder"))
        assert all( isinstance(action, BuilderAction) for action in self.game.actions[:4] )

    def test_captain_role(self):
        self.game.take_action(GovernorAction("Aa"))
        self.game.board["Aa"].corn = 3
        self.game.take_action(RoleAction("Aa", role="captain"))
        assert all( isinstance(action, CaptainAction) for action in self.game.actions[:4] )

    def test_craftsman_role(self):
        self.game.take_action(GovernorAction("Aa"))
        self.game.board["Aa"].tiles["corn_tile"] = WorkplaceData(2, 1)
        self.game.take_action(RoleAction("Aa", role="craftsman"))
        assert isinstance(self.game.actions[0], CraftsmanAction)

    def test_mayor_role(self):
        self.game.take_action(GovernorAction("Aa"))
        self.game.take_action(RoleAction("Aa", role="mayor"))
        assert all( isinstance(action, MayorAction) for action in self.game.actions[:4] )


    def test_settler_role(self):
        self.game.take_action(GovernorAction("Aa"))
        self.game.take_action(RoleAction("Aa", role="settler"))
        assert all( isinstance(action, SettlerAction) for action in self.game.actions[:4] )


    def test_trader_role(self):
        self.game.take_action(GovernorAction("Aa"))
        self.game.take_action(RoleAction("Aa", role="trader"))
        assert all( isinstance(action, TraderAction) for action in self.game.actions[:4] )
    
    def test_no_second_prospector(self):
        self.game.take_action(GovernorAction("Aa"))
        with self.assertRaises(AssertionError):
            self.game.take_action(RoleAction("Aa", role="second_prospector"))

class TestBoard3(unittest.TestCase):

    def setUp(self):
        self.board = Board.new("ABC")
    
    def test_new_board(self):
        self.assertEqual(len(self.board.towns), 3)
        self.assertIn('A', self.board.towns)
        self.assertIn('B', self.board.towns)
        self.assertIn('C', self.board.towns)
        self.assertEqual(self.board.money, 48)
        self.assertEqual(self.board.people, 55)
    
    def test_give_tile(self):
        town = self.board['A']
        tile = self.board.exposed_tiles[0]
        prev = town.tiles[tile].placed
        self.assertLessEqual(prev, 1)
        self.board.give_tile(tile, to=town)
        self.assertEqual(town.tiles[tile].placed, prev+1)

class TestTown(unittest.TestCase):

    def setUp(self):
        self.town = Town(name='TestTown')
    
    def test_new_town(self):
        self.assertEqual(self.town.name, 'TestTown')
        self.assertEqual(self.town.money, 0)
        self.assertIsNone(self.town.role)

    def test_production_corn(self):
        # Test when there are no workers on corn tile
        self.town.tiles["corn_tile"] = WorkplaceData(0, 0)
        self.assertEqual(self.town.production("corn"), 0)

        # Test when there are workers on corn tile
        self.town.tiles["corn_tile"] = WorkplaceData(2, 2)
        self.assertEqual(self.town.production("corn"), 2)

    def test_production_coffee(self):
        # Test when there are no coffee roasters
        self.town.tiles["coffee_tile"] = WorkplaceData(5, 2)
        self.assertEqual(self.town.production("coffee"), 0)

        # Test when there are coffee roasters, but no workers
        self.town.buildings["coffee_roaster"] = WorkplaceData(1, 0)
        self.assertEqual(self.town.production("coffee"), 0)

        # Test when there are coffee roasters and workers
        self.town.buildings["coffee_roaster"] = WorkplaceData(1, 1)
        self.assertEqual(self.town.production("coffee"), 1)

        # Test when there are more workers on coffee tile than coffee roasters
        self.town.tiles["coffee_tile"] = WorkplaceData(5, 5)
        self.assertEqual(self.town.production("coffee"), 1)

    def test_production_indigo(self):
        # Test when there are no indigo plants
        self.town.tiles["indigo_tile"] = WorkplaceData(3, 2)
        self.assertEqual(self.town.production("indigo"), 0)

        # Test when there are small indigo plants, but no workers
        self.town.buildings["small_indigo_plant"] = WorkplaceData(2, 0)
        self.assertEqual(self.town.production("indigo"), 0)

        # Test when there are small indigo plants and workers
        self.town.buildings["small_indigo_plant"] = WorkplaceData(2, 2)
        self.assertEqual(self.town.production("indigo"), 2)

        # Test when there are more workers on indigo tile than indigo plants
        self.town.tiles["indigo_tile"] = WorkplaceData(5, 5)
        self.assertEqual(self.town.production("indigo"), 2)

        # Test when there are indigo plants and workers
        self.town.buildings["indigo_plant"] = WorkplaceData(1, 1)
        self.assertEqual(self.town.production("indigo"), 3)

class TestConstants(unittest.TestCase):

    def test_buildings(self):
        self.assertEqual(len(BUILDINGS), 6+12+5)
        self.assertIn('tobacco_storage', BUILDINGS)
    
    def test_roles(self):
        self.assertEqual(len(ROLES), 8)
        self.assertIn('settler', ROLES)
    
    def test_goods(self):
        self.assertEqual(len(GOODS), 5)
        self.assertIn('coffee', GOODS)

if __name__ == '__main__':
    unittest.main()