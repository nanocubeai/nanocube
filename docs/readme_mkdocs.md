# CubedPandas website & documentation how-to guide
by Thomas Zeutschler, June 2024

## Introduction
The CubedPandas website & documentation is made with [MkDocs](https://www.mkdocs.org/). MkDocs is a static site generator that
creates a website from markdown files and from the actual source code of the project. The CubedPandas website will 
be hosted on GitHub pages: [https://zeutschler.github.io/cubedpandas/](https://zeutschler.github.io/cubedpandas/).

## How to build the documentation
The documentation can be built by using the `mkdocs` command line tool from the root directory of the project: 

```shell
mkdocs build --clean --site-dir 'pages/'
```

## How to deploy the documentation

To (re)build the static site in the `site/` directory use the following command.
Please only create the static content in the `site/` directory, do not commit the `site/` directory to the repository.
When the command as ask for credentials, just kill the process.
The actual upload to GitHub Pages will be performed by a GitHub Action 'static-site-upload.yml' which can
be triggered by pushing to the master branch.

```shell
mkdocs gh-deploy --clean  
```

## How to run and view the documentation locally
The documentation can be run and viewed locally by using the `mkdocs` command line tool from the root 
directory of the project
```shell
mkdocs serve
```
This will start a local web server that serves the documentation. Edits to the markdown files will be
automatically reloaded in the browser. The documentation is the available at the following URL:

```shell            
http://127.0.0.1:8000/data-model-generator/
```
To stop the local web server, press `CTRL+C` in the command line tool. That's all, **enjoy!**

Additional information on how to use MkDocs can be found in the [MkDocs documentation](https://www.mkdocs.org/)
and in the following guide [RealPython: Build Your Python Project Documentation With MkDocs](https://realpython.com/python-project-documentation-with-mkdocs/).

For GitHub Action setup please see
the [GitHub Action documentation](https://docs.github.com/en/actions/learn-github-actions).
and https://github.com/mkdocs/mkdocs/discussions/3432

