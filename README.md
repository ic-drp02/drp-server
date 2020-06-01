# NHS Guidelines App - Backend Server

## Running the app

To just get a server and database up and running as quickly as possible:

```
> docker-compose up
```

This will run the application in _roughly_ the same environment as production (i.e. with the production web server - Gunicorn).
The server runs on port 8000 and the database is on port 5432.
If you are working on the server itself, you probably want to use development mode. See below for instructions.

## Seeding the database

You can populate the database with test data from a json file. This is done by running the following command:

```sh
> flask seed [filename].json
```

You can optionally pass the `--drop-all` flag which will drop all existing data in the database and
recreate the tables before populating them with data.

There is an example json file [in this repo](seed_data.json). It would be helpful if we keep this up to date with useful seed data.

## Tips for local development

This isn't strictly neccessary but you probably want to install the dependencies in a python virtual environment to avoid conflicts.

Make sure you have python3-venv:

```sh
> sudo apt install python3-venv
```

Then in the project root run:

```sh
> python3 -m venv .venv             # Create the virtual environment
> source .venv/bin/activate         # Activate the virtual environment in your shell
> pip install -r requirements.txt   # Install project dependencies
```

Any time you open a new shell, you'll need to reactivate the venv:

```sh
> source .venv/bin/activate
```

If you ~~are a man of culture :)~~ use vscode with the python extension, this is done automatically when you open a terminal (in vscode of course).

If you don't want to do this you can just install the dependencies globally using just:

```sh
> pip install -r requirements.txt
```

But personally I prefer using virtual envs - less pollution in my environment.

## Running the app in development

Since we're gonna be using a database, you'll obviously need one locally for development - we don't want to mess with the actual database in development! You could manually install postgres, but that may or may not end up being a pain. The other option is to install docker and docker-compose and then just run

```sh
> docker-compose up db
```

in the project root. This will run postgres in a docker container on your machine, exposing it on port 5432 with a default database called `postgres`. The username is `postgres` and the password is `drp-dev`. To destroy the database just run

```sh
> docker-compose down
```

This is useful if you screw up something while playing around.

Once you have a database set up, you should run:

```sh
> flask db upgrade
```

This will run the database migrations, which creates all the tables. Then to run the flask app, you can run:

```sh
> export FLASK_ENV=development
> flask run
```

Nice and simple!

## Running the tests

You will need a database running in order to run the tests. See above for instructions on how to set this up. To set the uri of the database, run:

```sh
> export TEST_DATABASE_URI="postgresql://[USERNAME]:[PASSWORD]@[SERVER]:[PORT]/[DATABASE_NAME]"
```

By default if this environment variable is not set, the database from above is used. To run the tests:

```sh
> pytest tests -v
```

> :warning: **Running the tests will delete all data in the database!**

## Adding and modifying database models

The database schema is managed through migrations, which are basically python scripts that perform some update to the schema.
To add a new model, add it to the drp/models folder and make sure that it is exported in [drp/models/\_\_init\_\_.py](drp/models/__init__.py).
Then run:

```sh
> flask db migrate -m "A message describing the migration..."
```

This will generate a migration in the migrations/versions folder.
You should always double check this file to make sure it does what you want it to,
and you should probably run flake8 to format it so that the ci doesn't complain.

## Code style

I've set up flake8 for linting in the CI pipeline. In vscode, you can set the default linter to flake8 in the settings. I'm also using autopep8 locally in vscode for auto formatting. In PyCharm there's probably some way to setup linting and formatting but since I don't have it locally you'll have to play around with it. Lmk if it gets too annoying and we can maybe adjust stuff.
