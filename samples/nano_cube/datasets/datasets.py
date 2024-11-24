from pathlib import Path
import pandas as pd
from pathlib import Path
from datetime import datetime

def convert_to_parquet(file_path: str):
    df = pd.read_csv(file_path)
    df.to_parquet(file_path.replace(".csv", ".parquet"))

def simple_sales():
    """
    Returns a tuple of a Pandas dataframe and a CubedPandas schema (a Python dict).
    The dataframe is very simple and contains 3 columns (product, channel and sales) and just 6 rows.
    """
    data = {
        "product": ["A", "B", "C", "A", "B", "C"],
        "channel": ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
        "sales": [100, 150, 300, 200, 250, 350]
    }
    df = pd.DataFrame.from_dict(data)
    schema = {
        "dimensions": [
            {"column": "product"},
            {"column": "channel"}
        ],
        "measures": [
            {"column": "sales"}
        ]
    }
    return df, schema

def simple_sales_with_date():
    """
    Returns a tuple of a Pandas dataframe and a CubedPandas schema (a Python dict).
    The dataframe is very simple and contains 4 columns (product, channel, date and sales) and just 6 rows.
    """
    data = {
        "product": ["A", "B", "C", "A", "B", "C"],
        "channel": ["Online", "Online", "Online", "Retail", "Retail", "Retail"],
        "date": [datetime(2024,6,1), datetime(2024,6,2),
                 datetime(2024,7,1), datetime(2024,7,2),
                 datetime(2024,12,1), datetime(2024,12,2)],
        "sales": [100, 150, 300, 200, 250, 350]
    }
    df = pd.DataFrame.from_dict(data)
    schema = {
        "dimensions": [
            {"column": "product"},
            {"column": "channel"},
            {"column": "date"}
        ],
        "measures": [
            {"column": "sales"}
        ]
    }
    return df, schema

def supermarket_sales():
    """
    Returns a tuple of a Pandas dataframe and a CubedPandas schema (a Python dict).
    The dataframe is an example of supermarket sales data and contains 17 columns and 1000 rows.

    For documentation please visit https://www.kaggle.com/aungpyaeap/supermarket-sales.
    """
    # Columns:
    # Invoice ID,Branch,City,Customer type,Gender,Product line,Unit price,Quantity,Tax 5%,Total,Date,Time,Payment,cogs,gross margin percentage,gross income,Rating
    # 750-67-8428,A,Yangon,Member,Female,Health and beauty,74.69,7,26.1415,548.9715,1/5/2019,13:08,Ewallet,522.83,4.761904762,26.1415,9.1

    df = pd.read_csv("datasets/supermarket_sales.csv")  # containing 1.000 rows
    schema = {
        "dimensions": [
            {"column": "Date"},
            {"column": "Time"},
            {"column": "Invoice ID"},
            {"column": "Branch"},
            {"column": "City"},
            {"column": "Customer type"},
            {"column": "Gender"},
            {"column": "Product line"},
            {"column": "Payment"},
        ],
        "measures": [
            {"column": "Unit price"},
            {"column": "Quantity"},
            {"column": "Tax 5%"},
            {"column": "Total"},
            {"column": "cogs"},
            {"column": "gross margin percentage"},
            {"column": "gross income"},
            {"column": "Rating"},
        ]
    }
    return df, schema

def car_sales():
    """
    Returns a tuple of a Pandas dataframe and a CubedPandas schema (a Python dict).
    The dataframe contains a larger, real world dataset about car sales and contains 16 columns and ±500,000 rows.

    For documentation please visit https://www.kaggle.com/datasets/mystifoe77/car-prices.
    """
    # Columns:
    # year,make,model,trim,body,transmission,vin,state,condition,odometer,color,interior,seller,mmr,sellingprice,saledate
    # 2015,Kia,Sorento,LX,SUV,automatic,5xyktca69fg566472,ca,5,16639,white,black,kia motors america  inc,20500,21500,Tue Dec 16 2014 12:30:00 GMT-0800 (PST)


    # df = pd.read_csv(Path("datasets/car_prices.csv"))
    df = pd.read_parquet(Path("datasets/car_prices.parquet"))
    schema = {
        "dimensions": ["year",
                       "make" ,
                       "model",
                       "trim",
                       "body",
                       "transmission",
                       # "vin",
                       "state",
                       "condition",
                       "color",
                       "interior",
                       # "seller",
                       "saledate"
        ],
        "measures": [ "odometer", "mmr", "sellingprice"]
    }
    return df, schema


