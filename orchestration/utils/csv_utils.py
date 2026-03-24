"""CSV utilities"""

import csv
from typing import List, Dict


def read_csv(path: str) -> List[Dict]:
    """Read CSV file"""
    with open(path, 'r') as f:
        return list(csv.DictReader(f))


def write_csv(path: str, data: List[Dict], fieldnames: List[str] = None):
    """Write CSV file"""
    if not data:
        return
    fieldnames = fieldnames or list(data[0].keys())
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def read_csv_raw(path: str) -> List[List[str]]:
    """Read CSV raw"""
    with open(path, 'r') as f:
        return list(csv.reader(f))


def csv_to_dicts(path: str, key_field: str) -> Dict:
    """CSV to dict by key field"""
    rows = read_csv(path)
    return {row[key_field]: row for row in rows}
