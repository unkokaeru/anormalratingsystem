"""file_handling.py: File handling utilities for the application."""

import csv
from pathlib import Path

from . import logger

logger = logger.getChild(__name__)


def read_csv(file_path: Path) -> list[dict[str, str]]:
    """
    Read a CSV file and return the contents as a list of dictionaries.

    Parameters
    ----------
    file_path : Path
        Path to the CSV file to read.

    Returns
    -------
    list[dict[str, Any]]
        A list of dictionaries containing the data from the CSV file.

    Raises
    ------
    ValueError
        If the input file is not a CSV file.
    """
    logger.debug(f"Reading CSV file from {file_path}")

    if file_path.suffix != ".csv":
        logger.error(f"Input file {file_path} is not a CSV file.")
        raise ValueError("Input file must be a CSV file.")

    with open(file_path) as file:
        csv_reader = csv.DictReader(file)
        logger.debug(f"CSV file read successfully from {file_path} as {csv_reader}")
        return list(csv_reader)


def write_csv(file_path: Path, data: list[dict[str, str]]) -> None:
    """
    Write a list of dictionaries to a CSV file.

    Parameters
    ----------
    file_path : Path
        Path to the CSV file to write.
    data : list[dict[str, str]]
        List of dictionaries to write to the CSV file.

    Raises
    ------
    ValueError
        If the output file is not a CSV file.
    """
    logger.debug(f"Writing CSV file to {file_path}")

    if file_path.suffix != ".csv":
        logger.error(f"Output file {file_path} is not a CSV file.")
        raise ValueError("Output file must be a CSV file.")

    with open(file_path, "w") as file:
        csv_writer = csv.DictWriter(file, fieldnames=data[0].keys())
        csv_writer.writeheader()
        csv_writer.writerows(data)

    logger.debug(f"CSV file written successfully to {file_path}")
