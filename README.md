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

TODO: Document migrations when we actually start using the database

Then to run the flask app, you can run:

```sh
> export FLASK_ENV=development
> flask run
```

Nice and simple!

## Code style

I've set up flake8 for linting in the CI pipeline. In vscode, you can set the default linter to flake8 in the settings. I'm also using autopep8 locally in vscode for auto formatting. In PyCharm there's probably some way to setup linting and formatting but since I don't have it locally you'll have to play around with it. Lmk if it gets too annoying and we can maybe adjust stuff.

## Accessing the staging server

You can access the deployed application at http://146.169.42.170:8000.

Unfortunately, this is an internal IP address so you'll need to either connect to the Imperial VPN (I've never gotten it to work), or use SSH tunnelling. This can be done by running:

```sh
> ssh -N -D 12345 YOUR_USERNAME@shell1.doc.ic.ac.uk
```

and then configuring your web browser or OS to proxy traffic over port 12345.

- On Chrome/Edge [this](https://chrome.google.com/webstore/detail/proxy-switchyomega/padekgcemlokbadohgkifijomclgjgif) is a nice extension.
- On Firefox you can play around in the network settings.
