<img src="logo.svg" alt="Flickypedia, by Flickr.org">

Flickypedia is a tool to copy openly licensed photos from Flickr to Wikimedia Commons.

## Key pieces

*   Wikimedia OAuth 2.0
*   Wikimedia APIs for upload
*   Flickr APIs for download
*   Celery for background processing

## How to understand the codebase

* __init__.py
* views
* templates
  * everything is named after URL paths
  * show steps as a Mermaid diagram
* assets

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
$ coverage run -m pytest tests
$ coverage report
```

* What keys do you need?
* How do you run the app?

## How to run the background worker

```console
$ celery --app flickypedia.celery_app worker --loglevel INFO
```