import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="flickypedia",
        description="Run a local version of flickypedia, a tool to copy CC-licensed photos from Flickr to Wikimedia Commons.",
    )

    parser.add_argument("--port", help="the port to bind to", type=int, default=5001)
    parser.add_argument("--host", default="127.0.0.1", help="the interface to bind to")
    parser.add_argument("--debug", action="store_true", help="run in debug mode")

    args = parser.parse_args()

    from flickypedia.app import app

    app.run(debug=args.debug, port=args.port, host=args.host)
