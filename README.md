# NHS Guidelines App - Backend Server

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

## Running the app

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

## Code style

I've set up flake8 for linting in the CI pipeline. In vscode, you can set the default linter to flake8 in the settings. I'm also using autopep8 locally in vscode for auto formatting. In PyCharm there's probably some way to setup linting and formatting but since I don't have it locally you'll have to play around with it. Lmk if it gets too annoying and we can maybe adjust stuff.
