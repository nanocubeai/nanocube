# nanocube - Copyright (c)2024, Thomas Zeutschler, MIT license

import unittest
import pandas as pd
from nanocube import Cube

class TestNanoCube(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame({'customer': ['A', 'B', 'A', 'B', 'A'],
                           'product': ['P1', 'P2', 'P3', 'P1', 'P2'],
                           'promo': [True, False, True, True, False],
                           'sales': [100, 200, 300, 400, 500],
                           'cost': [60, 90, 120, 200, 240]})

    def test_cube_methods(self):
        cube = Cube(self.df)
        self.assertEqual(cube.get(customer='A', product='P1'), {'sales': 100, 'cost': 60})
        self.assertEqual(cube.get(customer='A'), {'sales': 900, 'cost': 420})
        self.assertEqual(cube.get(product=['P1', 'P2']), {'sales': 1200, 'cost': 590})
        self.assertEqual(cube.get(promo=True), {'sales': 800, 'cost': 380})
        self.assertEqual(cube.get('sales', promo=True), 800)
        self.assertEqual(cube.get('sales'), 1500)
        self.assertEqual(cube.get('sales', 'cost', customer='A'), [900, 420])

    def test_cube_alternative_initializations(self):
        cube = Cube(self.df, dimensions=['customer', 'product'], measures=['sales', 'cost'])
        self.assertEqual(cube.get(customer='A', product='P1'), {'sales': 100, 'cost': 60})
        self.assertEqual(cube.get(customer='A'), {'sales': 900, 'cost': 420})
        self.assertEqual(cube.get(product=['P1', 'P2']), {'sales': 1200, 'cost': 590})

        cube = Cube(self.df, dimensions=['promo'], measures=['sales'])
        self.assertEqual(cube.get('sales', promo=True), 800)
        self.assertEqual(cube.get(promo=True), {'sales': 800})
        self.assertEqual(cube.get('sales'), 1500)

    def test_cube_accessor(self):
        cube = self.df.nanocube.cube
        self.assertEqual(cube.get(customer='A', product='P1'), {'sales': 100, 'cost': 60})
        self.assertEqual(cube.get(customer='A'), {'sales': 900, 'cost': 420})
        self.assertEqual(cube.get(product=['P1', 'P2']), {'sales': 1200, 'cost': 590})
        self.assertEqual(cube.get(promo=True), {'sales': 800, 'cost': 380})
        self.assertEqual(cube.get('sales', promo=True), 800)
        self.assertEqual(cube.get('sales'), 1500)
        self.assertEqual(cube.get('sales', 'cost', customer='A'), [900, 420])



if __name__ == '__main__':
    unittest.main()
