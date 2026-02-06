import argparse


def setup_delete_parser():
    """Setup parser for file deletion."""
    parser = argparse.ArgumentParser(
        prog="File Deleter",
        description="Delete existing files",
    )

    parser.add_argument(
        "-d",
        "--delete-processed",
        action="store_true",
    )

    parser.add_argument(
        "-d-benefits",
        "--delete-benefits",
        action="store_true",
    )

    return parser.parse_args()
