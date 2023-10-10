# flickypedia

This is a tool to copy Creative Commons-licensed photos from Flickr to Wikimedia Commons.

It's in its initial stages, but check back soon for more info!

## Development

You can set up a local development environment by cloning the repo and installing dependencies:

```console
$ git clone https://github.com/Flickr-Foundation/flickypedia.git
$ cd flinumeratr
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -e .
```

If you want to run tests, install the dev dependencies and run `coverage`:

```console
$ source .venv/bin/activate
$ pip install -r dev_requirements.txt
$ coverage run -m pytest tests; coverage report
```
