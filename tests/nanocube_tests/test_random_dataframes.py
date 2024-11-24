# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from unittest import TestCase
from nanocube import Cube
from nanocube import cubed


class TestCube(TestCase):

    def create_df(self, dimensions: int, measures: int, rows: int, include_nans: bool = False, seed: int = 42):
        data = {}
        random.seed(seed)
        for i in range(dimensions):
            data_type = random.choice(["string", "date", "bool"])
            if data_type == "string":
                data[f"dim{i}"] = pd.array([f"dim{i}_{j}" for j in range(rows)], dtype="string")
            elif data_type == "date":
                data[f"dim{i}"] = pd.array([str(datetime.now().date() + timedelta(days=j)) for j in range(rows)],
                                           dtype="datetime64")
            elif data_type == "bool":
                data[f"dim{i}"] = pd.array([random.choice([True, False]) for j in range(rows)], dtype="bool")

        for i in range(measures):
            data_type = random.choice(["float", "int"])
            if data_type == "float":
                data[f"measure{i}"] = pd.array([round(number=random.random() * 100, ndigits=2) for j in range(rows)],
                                               dtype="float")
            elif data_type == "int":
                data[f"measure{i}"] = pd.array([random.randint(1, 100) for j in range(rows)], dtype="int")

        if include_nans:
            for i in range(measures):
                nan_indices = random.sample(range(rows), k=int(rows * 0.05))
                for j in nan_indices:
                    data[f"measure{i}"][j] = 0
                for i in range(dimensions):
                    nan_indices = random.sample(range(rows), k=int(rows * 0.05))
                    for j in nan_indices:
                        data[f"dim{i}"][j] = np.NaN

        return pd.DataFrame(data)

    def test_measures_only_cube(self):

        for i in range(10):
            df = self.create_df(dimensions=10, measures=4, rows=100)
            cube = Cube(df)

            # check if all measures are present and the values are correct
            for measure in cube.schema.measures:
                a = float(df[measure.column].sum())
                b = cube[measure.column].numeric_value
                self.assertEqual(a, b)

            for dimension in cube.schema.dimensions:
                member = random.choice(list(dimension.members))
                measure = random.choice(cube.schema.measures)
                a = df[df[dimension.name] == member][measure.column].sum()
                b = cube[{dimension.name: member}, measure.column].numeric_value
                self.assertEqual(a, b)
