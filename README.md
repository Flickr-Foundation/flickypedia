<img src="logo.svg" alt="Flickypedia, by Flickr.org">

Flickypedia is a bridge between photos on Flickr and files on Wikimedia Commons.
It includes:

*   A web app for copying openly-licensed photos from Flickr to Wikimedia Commons ("uploadr")
*   A bot for improving the [structured data][sdc] for Flickr photos which are already on Wikimedia Commons ("backfillr")
*   A tool for getting data and statistics about Flickr photos on Wikimedia Commons ("extractr")

Our goal is that it results in higher quality records on Wikimedia Commons, with better connected data, better descriptive information, and makes it easier for Flickr photographers to see how their photos are being used.

Flickypedia was built by the US 501(c)(3) [Flickr Foundation] in 2023 in partnership with the Culture and Heritage team at [the Wikimedia Foundation].

[sdc]: https://commons.wikimedia.org/wiki/Commons:Structured_data
[Flickr Foundation]: https://www.flickr.org/
[the Wikimedia Foundation]: https://wikimediafoundation.org/

## Usage

If you want to copy some photos from Flickr to Wikimedia Commons, you can use the web app at <https://www.flickr.org/tools/flickypedia/>

If you want to use the `backfillr` or `extractr` tools, you need to clone the repo and install dependencies:

```console
$ git clone https://github.com/Flickr-Foundation/flickypedia.git
$ cd flinumeratr
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -e .
```

Then run the `flickypedia` CLI, which has help text that will explain what to do next:

```console
$ flickypedia --help
```

## Architecture

The Flickypedia code lives in the `src` folder, which is split into four main components:

*   **External APIs (`apis`)** – code for interacting with external services, including Flickr, SDC, and Wikimedia Commons.
    This is reasonably generic and not be too specific to Flickypedia.
    If you're looking for pieces to reuse, this is a good place to start looking.

*   **Uploadr** – a web app for copying openly-licensed photos from Flickr to Wikimedia Commons.
    This is a Flask app.

    The app is organised into a series of screens ("get photos", "select photos", "prepare info", and so on) – all the files associated with a screen are named to match the URL.
    e.g. the "prepare info" screen is at `/prepare_info`, so the associated files are `prepare_info.py`, `prepare_info.html`, `prepare_info.scss`, and so on.

*   **Backfillr** – a CLI for updating SDC for Flickr photos that have already been uploaded to Commons.
    You can either run on a single file or many files at once.

    It fetches the existing SDC for a photo, finds the Flickr ID, then calculates the "new" SDC for the photo (if it was uploaded with Flickypedia today).
    It compares the new and existing SDC, and writes any missing statements back into Commons.

*   **Extractr** – a CLI for getting data about existing Flickr photos on Commons from SDC snapshots.

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


