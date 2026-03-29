"""CSV utilities"""

import csv


def read_csv(path: str) -> list[dict]:
    """Read CSV file"""
    with open(path) as f:
        return list(csv.DictReader(f))


def write_csv(path: str, data: list[dict], fieldnames: list[str] = None):
    """Write CSV file"""
    if not data:
        return
    fieldnames = fieldnames or list(data[0].keys())
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def read_csv_raw(path: str) -> list[list[str]]:
    """Read CSV raw"""
    with open(path) as f:
        return list(csv.reader(f))


def csv_to_dicts(path: str, key_field: str) -> dict:
    """CSV to dict by key field"""
    rows = read_csv(path)
    return {row[key_field]: row for row in rows}
