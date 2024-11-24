# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file
import random

import numpy as np
import pandas as pd
from unittest import TestCase

from nanocube import Cube
from nanocube import cubed


class TestRealWorldDatasets(TestCase):
    """
    The aim of this case is automatically test CubedPandas against
    a (hopefully) growing set of real-world datasets from various sources and
    ideally also actual users of CubedPandas. Whenever a dataset creates
    problems, the dataset should be added to the `datasets` folder to ensure that
    the problem is fixed and does not reappear in the future.

    For performance reasons, the datasets should be kept small and simple, just
    containing a few, ideally error-causing rows. The datasets should be available
    as CSV files, other files will not be loaded. If a dataset is not loadable by
    Pandas itself, it will also not be tested, as CubedPandas anyhow relies on an
    existing Pandas DataFrame to do it's work.

    Approach:
    All files in the `datasets` folder will be loaded and tested against various
    CubedPandas functions. The automated tests will be kept simple and only check for the
    absence of exceptions.
    """

    def setUp(self) -> None:
        # get all datasets from folder `datasets`
        self.debug = self.is_debug()
        import pathlib
        files = [{"path": file.absolute(), "name": file.name} for file in pathlib.Path('datasets/').glob('**/*') if
                 file.name.endswith('.csv')]
        self.files = sorted(files, key=lambda d: d['name'])

    @staticmethod
    def is_debug():
        import sys
        gettrace = getattr(sys, 'gettrace', None)
        if gettrace is None:
            return False
        else:
            v = gettrace()
            if v is None:
                return False
            else:
                return True

    def test_measures_only_cube(self):
        for file in self.files:
            try:
                df = pd.read_csv(file["path"])
            except pd.errors.ParserError:
                continue  # skip files that cannot be loaded by Pandas, not of interest for testing
            if self.debug:
                print(f"\n{file['name']} {'#' * (80 - len(file['name']))}")
            self.do_test_dataset(file["name"], df)

    def do_test_dataset(self, file_name, df):
        cube = cubed(df)

        num_records = len(cube)
        # 1. read totals for all measures in the cube
        for measure in cube.schema.measures:
            value = cube[measure]
            if self.debug:
                print(f"{file_name}: Total of measure '{measure}' = {value}")

        # 2. filter measure, we use the average value as a filter
        for measure in cube.schema.measures:
            filter_value = cube[measure].avg
            test_value = cube[cube[measure]._ < filter_value]
            if self.debug:
                print(f"{file_name}: Sum of values below average for measure '{measure}' = {test_value}")

        # 3. read values from max. 4x random members from all dimensions for all measures
        for measure in cube.schema.measures:
            for dimension in cube.schema.dimensions:
                members = random.sample(list(dimension.members), min(4, len(dimension.members)))
                for member in members:
                    if str(member).lower().strip() == 'nan':
                        a = df[df[dimension.name].isna()][measure.column].sum()
                    else:
                        a = df[df[dimension.name] == member][measure.column].sum()
                    b = cube[{dimension.name: member}, measure.column].sum()

                    if self.debug:
                        print(f"{file_name}: cube[{{'{dimension.name}:{member}'}}, '{measure}'] = {a}")
                    self.assertEqual(a, b)
