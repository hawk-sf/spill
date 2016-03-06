Spill
=====

A utility for generating Flask scaffolding and boilerplate. Very early
stage. The aim is to be simple: no YAML or configuration files, just
pass along a few arguments.

::

    spill foo -b api main -m user group --db-type sqlite --db-orm sqlalchemy

creates:

::

    ./foo/
        |-- .gitignore
        |-- config.py
        |-- manage.py
        |-- README.md
        |-- requirements.py
        |-- /app
            |-- __init__.py
            |-- models.py
            |-- /api
                |-- __init__.py
                |-- errors.py
                |-- forms.py
                |-- views.py
            |-- /main
                |-- __init__.py
                |-- errors.py
                |-- forms.py
                |-- views.py
        |-- /templates

Usage
-----

::

    usage: spill [-h] [-b BLUEPRINTS [BLUEPRINTS ...]] [-m MODELS [MODELS ...]]
                 [--db-type [{sqlite,mysql,mongodb}]]
                 [--db-orm [{sqlalchemy,mongoengine}]] [--no-forms]
                 [--no-templates]
                 [project]

    Creates scaffolding and boilerplate for a Flask application.

    positional arguments:
      project               Name of Flask project to spill. If no project
                            specified, will assume CWD is the project directory.

    optional arguments:
      -h, --help            show this help message and exit
      -b BLUEPRINTS [BLUEPRINTS ...], --blueprints BLUEPRINTS [BLUEPRINTS ...]
                            A list of blueprints to create (Defaults: 'main' and
                            'api')
      -m MODELS [MODELS ...], --models MODELS [MODELS ...]
                            A list of model objects
      --db-type [{sqlite,mysql,mongodb}]
                            The type of database you will use
      --db-orm [{sqlalchemy,mongoengine}]
                            The ORM you will use
      --no-forms            No Flask-WTF forms
      --no-templates        No Jinja2 templates

Currently built with/for Python 2.7.

Installation
============

::

    pip install spill
