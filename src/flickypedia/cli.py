import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="flickypedia",
        description="Run a local version of flickypedia, a tool to copy CC-licensed photos from Flickr to Wikimedia Commons.",
    )

    parser.add_argument("--port", help="the port to bind to", type=int, default=5000)
    parser.add_argument("--host", default="127.0.0.1", help="the interface to bind to")
    parser.add_argument("--debug", action="store_true", help="run in debug mode")

    args = parser.parse_args()

    from flickypedia import create_app

    app = create_app(data_directory="data", debug=args.debug)

    if app.config["OAUTH2_PROVIDERS"]["wikimedia"]["client_id"] is None:
        sys.exit("No Wikimedia client ID provided! Set WIKIMEDIA_CLIENT_ID.")

    if app.config["OAUTH2_PROVIDERS"]["wikimedia"]["client_secret"] is None:
        sys.exit("No Wikimedia client secret provided! Set WIKIMEDIA_CLIENT_SECRET.")

    app.run(debug=args.debug, port=args.port, host=args.host)
