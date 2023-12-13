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


