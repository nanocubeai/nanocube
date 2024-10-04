# -*- coding: utf-8 -*-
# setup.py for cubedpandas

from setuptools import setup
from setuptools import find_packages
from nanocube import VERSION as NANOCUBE_VERSION


# ...to run the build and deploy process to pypi.org manually:
# 0. delete folder 'build'
# 1. empty folder 'dist'
# 2. python3 setup.py sdist bdist_wheel   # note: Wheel need to be installed: pip install wheel
# 3. twine upload -r  pypi dist/*         # note: Twine need to be installed: pip install twine

# ... via Github actions
# https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/

VERSION = NANOCUBE_VERSION
DESCRIPTION = "NanoCube - Lightning fast OLAP-style point queries on Pandas DataFrames."
LONG_DESCRIPTION = """
NanoCube is a super minimalistic, in-memory OLAP cube implementation for lightning fast point queries
upon Pandas DataFrames. It consists of only 27 lines of magical code that turns any DataFrame into a 
multi-dimensional OLAP cube. NanoCube shines when multiple point queries are needed on the same DataFrame,
e.g. for financial data analysis, business intelligence or fast web services.

For aggregated point queries NanoCube is 100x to 1,000x times faster than Pandas. For the special purpose,
NanoCube is also much faster than all other libraries, like Spark, Polars, Modin, Dask or Vaex. If such 
libraries are drop-in replacements with Pandas dataframe, you should be able to use them with NanoCube too.
"""

setup(

    name="nanocube",
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    classifiers=[
        "Topic :: Utilities",
        "Topic :: Database",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",

        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",

        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
    ],
    author="Thomas Zeutschler",
    keywords=['python', 'pandas', 'numpy', 'spark', 'data analysis', 'OLAP', 'cube', 'dataframe', ],
    author_email="cubedpandas@gmail.com",
    url="https://github.com/Zeutschler/nanocube",
    license='MIT',
    platforms=['any'],
    zip_safe=True,
    python_requires='>= 3.10',
    install_requires=[
        'numpy',
        'pandas',
        'pyroaring',
    ],
    test_suite="nanocube.tests",
    packages=['nanocube'],  # , 'tests'],
    project_urls={
        'Homepage': 'https://zeutschler.github.io/nanocube/',
        'Documentation': 'https://zeutschler.github.io/nanocube/',
        'GitHub': 'https://github.com/Zeutschler/nanocube',
    },
)