import argparse
from pathlib import Path
from controllers.controller import Controller
from pathlib import Path
import sys


def get_asset_path() -> Path:
    """ Get the absolute path to an asset in the assets folder. """
    if hasattr(sys, '_MEIPASS'):
        # Running from a bundled executable
        base_path = Path(sys._MEIPASS)
    else:
        # Running from the source code
        base_path = Path(__file__).resolve().parent

    print(f"asset basepath: {base_path}")
    return base_path

def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="PicPyles Application")
    parser.add_argument(
        "file_path",
        type=Path,
        nargs="?",
        default=None,
        help="Optional path to the file or directory to load."
    )
    return parser.parse_args()

def main() -> None:
    """
    The main entry point for the application. Parses arguments, initializes
    the Controller with the provided path (if any), and starts the application's main loop.
    """
    assetspath = get_asset_path()
    args = parse_args()
    controller = Controller(assetspath, path=args.file_path)
    controller.run()

if __name__ == "__main__":
    main()
