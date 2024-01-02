import unittest
from .boards import Board
from .towns import Town
from .constants import BUILDINGS, ROLES, GOODS

class TestBoard3(unittest.TestCase):

    def setUp(self):
        self.board = Board.new(['Alice', 'Bob', 'Charlie'])
    
    def test_new_board(self):
        self.assertEqual(len(self.board.towns), 3)
        self.assertIn('Alice', self.board.towns)
        self.assertIn('Bob', self.board.towns)
        self.assertIn('Charlie', self.board.towns)
        self.assertEqual(self.board.money, 48)
        self.assertEqual(self.board.people, 55)
    
    def test_give_tile(self):
        alice = self.board['Alice']
        tile = self.board.exposed_tiles[0]
        prev = alice.tiles[tile].placed
        self.assertLessEqual(prev, 1)
        self.board.give_tile(tile, to=alice)
        self.assertEqual(alice.tiles[tile].placed, prev+1)

class TestTown(unittest.TestCase):

    def setUp(self):
        self.town = Town(name='TestTown')
    
    def test_new_town(self):
        self.assertEqual(self.town.name, 'TestTown')
        self.assertEqual(self.town.money, 0)
        self.assertIsNone(self.town.role)

    # def test_give_building(self):
    #     self.town.give_building('tobacco_storage')
    #     self.assertEqual(self.town.buildings['tobacco_storage'].placed, 1)

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