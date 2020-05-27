# NHS Guidelines App - Backend Server

## Tips for local development

This isn't strictly neccessary but you probably want to install the dependencies in a python virtual environment to avoid conflicts.

Make sure you have python3-venv:

```
> sudo apt install python3-venv
```

Then in the project root run:

```
> python3 -m venv .venv             # Create the virtual environment
> source .venv/bin/activate         # Activate the virtual environment in your shell
> pip install -r requirements.txt   # Install project dependencies
```

Any time you open a new shell, you'll need to reactivate the venv:

```
> source .venv/bin/activate
```

If you don't want to do this you can just install the dependencies globally using just:

```
> pip install -r requirements.txt
```

But personally I prefer using virtual envs - less pollution in my environment.

## Accessing the staging server

You can access the deployed application at http://146.169.42.170:8000.

Unfortunately, this is an internal IP address so you'll need to either connect to the Imperial VPN (I've never gotten it to work), or use SSH tunnelling. This can be done by running:

```
> ssh -N -D 12345 YOUR_USERNAME@shell1.doc.ic.ac.uk
```

and then configuring your web browser or OS to proxy traffic over port 12345.

- On Chrome/Edge [this](https://chrome.google.com/webstore/detail/proxy-switchyomega/padekgcemlokbadohgkifijomclgjgif) is a nice extension.
- On Firefox you can play around in the network settings.
