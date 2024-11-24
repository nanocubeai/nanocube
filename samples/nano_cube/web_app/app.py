# CubedPandas - Copyright (c)2024, Thomas Zeutschler, see LICENSE file

# CubedPandas - Sample Application
# --------------------------------
# A minimal FastAPI server that serves a CubedPandas Slice as an HTML table.
# The slice is created from a random selection of dimensions from a
# cube based on the dataset 'data.csv'. A Bootstrap based html template
# is used for styling, see 'template.html'.

import random
import uvicorn
import socket
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.responses import FileResponse

import pandas as pd
from nanocube import cubed

# (1) load a sample datasets
dataset = pd.read_csv("data.csv")
html_template = Path("template.html").read_text()

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def root():
    # (2) turn the dataset into a CubedPandas `Cube`
    cube = cubed(dataset, exclude = ["Invoice ID", "Date", "Time"])

    # (3) create a randomly generated CubedPandas `Slice`
    rows = random.sample(cube.schema.dimensions.to_list(), k=random.randint(1, 4))
    columns = None
    if len(rows) >= 3:
        columns = rows[len(rows)-1]
        rows = rows[:len(rows)-1]
    slice = cube.slice(rows=rows, columns=columns)

    # (4) wrap the slice into nice html
    slice_html_table = slice.to_html(classes=["table", "table-sm"])
    style = 'style="white-space:nowrap;"'
    slice_html_table = slice_html_table.replace("<table", f"<table style='{style}'")
    return html_template.format(table=slice_html_table)


@app.get("/logo.png", response_class=FileResponse)
async def logo():
    return  FileResponse("logo.png", media_type="image/png")


@app.get("/data.csv", response_class=FileResponse)
async def logo():
    return  FileResponse("data.csv", media_type="text/csv")


if __name__ == "__main__":
    host_name = socket.gethostbyname(socket.gethostname())
    uvicorn.run("app:app", host=host_name, port=8000, log_level="debug")
