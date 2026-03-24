"""CSV tools utilities"""

import csv


def csv_reader(file):
    """CSV reader"""
    return csv.reader(file)


def csv_writer(file):
    """CSV writer"""
    return csv.writer(file)
