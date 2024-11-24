# CubedPandas - A minimalistic web app using FastAPI

This a minimalistic web app example using FastAPI to demonstrate the use of CubedPandas.
It simply (1) loads a sample Pandas dataframe, (2) turns it CubedPandas `Cube`, (3) creates a randomly generated CubedPandas `Slice`,
(4) turns the slice into html using the `slice.to_html()` method and finally (5) serves the result to the user.

The template uses [Boostrap](https://getbootstrap.com), a great tool for creating responsive web pages.

> **Tip:**  You can easily extend this example to create a more complex web app with more features,  
>           e.g. add a dropdown to provide different datasets or different views/slices upon the data.

Here's the most relevant code from the main app file `app.py`:

```python
# (1) load a sample dataset
df: pd.DataFrame = pd.read_csv("data.csv")
html_template = Path("template.html").read_text()

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def root():
    # (2) turn the dataset into a CubedPandas `Cube`
    cdf = cubed(df, exclude=["Invoice ID", "Date", "Time"])

    # (3) create a randomly generated CubedPandas `Slice`
    rows = random.sample(cdf.dimensions.to_list(), k=random.randint(1, 4 ))
    columns = None
    if len(rows) >= 3:
        columns = rows[len(rows)-1]
        rows = rows[:len(rows)-1]
    slice = cdf.slice(rows=rows, columns=columns)

    # (4) turn the slice into html using the `slice.to_html()` method
    # (5) serve the result to the user.
    return html_template.format(table=slice.to_html(classes=["table", "table-sm"]))
```
