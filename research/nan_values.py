import numpy as np

a = np.array([0., np.nan, 2., np.nan, 2., 1., 0., 1., 2., 0.])
print(np.unique(a, equal_nan=True, axis=0, return_inverse=True))

a = np.array(['A', np.nan, 'B', np.nan, 'C'])
print(np.unique(a, equal_nan=True, axis=0, return_inverse=True))