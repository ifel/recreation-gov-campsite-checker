import argparse
from datetime import datetime


INPUT_DATE_FORMAT = "%Y-%m-%d"


def format_date(date_object):
    date_formatted = datetime.strftime(date_object, "%Y-%m-%dT00:00:00Z")
    return date_formatted


def format_date_request(date_object):
    date_formatted = datetime.strftime(date_object, "%Y-%m-%dT00:00:00.000Z")
    return date_formatted


def valid_date(s):
    try:
        return datetime.strptime(s, INPUT_DATE_FORMAT)
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)
