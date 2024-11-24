# NanoCube - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

from typing import Literal

import numpy as np
import pandas as pd


class DimensionStatistics:
    """
    Provides various statistical information about the members of a dimension.
    """

    def __init__(self, dimension):
        self._dimension = dimension
        self._members = dimension.members
        pass

    def summary(self):
        """
        Returns:
            Return a summary of the statistics.
        """
        raise NotImplementedError()

    def plot(self, measures=None):
        """

        Plots statistics for the members of the dimension and certain measures of the cube.
        If no measures are provided, only statistics for the default measure will be plotted.

        Args:
            measures: A list of measures to plot statistics for. If None, only the default measure
                of the cube will be plotted.

        Returns:
            Return one or multiple plots, renderer using matplotlib.
        """

        if measures is None:
            measures = [self._dimension.cube.default, ]

        for measure in measures:
            data = self._dimension.cube._pivot_table[measure].value_counts(dropna=False, ascending=False)
            data.plot(kind='hist', bins=20, title=f'{measure} Histogram')

    def outliers(self, measure,
                 method: Literal["iqr", "zscore", "mahalanobis", "lof", "isolation_forest", "oneclass_svm"] = "iqr"):
        """
        Returns:
            Return a list of members that are considered outliers.
        """
        # https://medium.com/@xai4heat/multivariate-outlier-detection-a-game-changer-in-understanding-complex-systems-deaad99e79f8

        raise NotImplementedError()

    @staticmethod
    def _get_outliers_zscore(df, threshold):
        df = df[["tsp", "deltae"]]
        df.dropna()
        d = df["deltae"]
        z_scores = np.where(d != 0, (d - np.mean(d[d != 0])) / np.std(d[d != 0]), np.nan)
        z_scores = np.abs(z_scores)
        outliers = df[abs(z_scores) > threshold][["tsp", "deltae"]]
        return outliers

    @staticmethod
    def _get_outliers_pca(df, threshold, components):
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler

        df = df[["tsp", "deltae"]]
        df.dropna()
        features = ["tsp", "deltae"]
        nan_mask = df.isna().any(axis=1)
        zero_mask = (df == 0).all(axis=1)
        exclude_mask = nan_mask | zero_mask
        x = df[~exclude_mask]
        x = df[features]
        x.fillna(0, inplace=True)
        scaler = StandardScaler()
        x_std = scaler.fit_transform(x)
        pca = PCA(n_components=components)
        pca.fit(x_std)
        x_pca = pca.transform(x_std)
        mahalanobis_distance = np.sqrt(np.sum(x_pca ** 2, axis=1))
        outliers_pca = df[mahalanobis_distance > threshold]
        outliers_pca = outliers_pca[outliers_pca["deltae"] != 0]
        return outliers_pca

    @staticmethod
    def get_outliers_isolation_forest(df, contamination):
        from sklearn.ensemble import IsolationForest

        features = ["tsp", "deltae"]
        df = df[features]
        df.fillna(0, inplace=True)
        model = IsolationForest(contamination=contamination)
        model.fit(df)
        outliers = model.predict(df)
        df["is_outlier"] = outliers
        df = df[df["deltae"] != 0]
        df = df[df["is_outlier"] == -1]
        return df[["tsp", "deltae"]]

    @staticmethod
    def get_outliers_mahalanobis_distances(df, threshold):
        from scipy.spatial.distance import mahalanobis

        df = df[["tsp", "deltae"]]
        df.fillna(0, inplace=True)
        deltae_data = df["deltae"].values
        tsp_data = df["tsp"].values
        data = np.column_stack((deltae_data, tsp_data))
        mean = np.nanmean(data, axis=0)
        stddev = np.nanstd(data, axis=0)
        normalized_data = (data - mean) / stddev
        nan_mask = np.isnan(normalized_data).any(axis=1)
        zero_mask = (normalized_data == 0).all(axis=1)
        remove_mask = nan_mask | zero_mask
        filtered_normalized_data = normalized_data[~remove_mask]
        normalized_data = filtered_normalized_data
        cov_matrix = np.cov(normalized_data, rowvar=False)
        mahalanobis_distances = [mahalanobis(point, mean, np.linalg.inv(cov_matrix)) for point in normalized_data]
        mahalanobis_distances_zscores = [(x - np.mean(mahalanobis_distances)) / np.std(mahalanobis_distances)
                                         for x in mahalanobis_distances]
        outliers_multivariate = [i for i, distance in enumerate(mahalanobis_distances) if
                                 mahalanobis_distances_zscores[i] > threshold]
        dhr = df.reset_index()
        dhr.rename(columns={"index": "DatetimeIndex"}, inplace=True)
        dhr = dhr[dhr.index.isin(outliers_multivariate)]
        dhr["Unnamed: 0"] = pd.to_datetime(dhr["Unnamed: 0"])
        dhr.set_index("Unnamed: 0", inplace=True)
        dhr = dhr[dhr["deltae"] != 0]
        return dhr[["tsp", "deltae"]]

    @staticmethod
    def get_outliers_hotelling(df, alpha):
        from scipy.stats import f

        df = df[["tsp", "deltae"]]
        df.fillna(0, inplace=True)
        X = df.values
        mean_vector = np.nanmean(X, axis=0)
        cov_matrix = np.cov(X, rowvar=False)
        n = len(X)
        p = X.shape[1]
        t_squared = np.zeros(n)
        for i in range(n):
            x_diff = X[i] - mean_vector
            t_squared[i] = np.dot(np.dot(x_diff, np.linalg.inv(cov_matrix)), x_diff)
        df1 = p
        df2 = n - p - 1
        critical_value = f.ppf(1 - alpha, df1, df2)
        outliers = np.where(t_squared > critical_value)[0]
        dhr = df.reset_index()
        dhr.rename(columns={"index": "DatetimeIndex"}, inplace=True)
        dhr = dhr[dhr.index.isin(outliers)]
        dhr["Unnamed: 0"] = pd.to_datetime(dhr["Unnamed: 0"])
        dhr.set_index("Unnamed: 0", inplace=True)
        dhr = dhr[dhr["deltae"] != 0]
        return dhr
