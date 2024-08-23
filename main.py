import argparse
from pathlib import Path
from controllers.controller import Controller

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
    args = parse_args()
    controller = Controller(path=args.file_path)
    controller.run()

if __name__ == "__main__":
    main()
