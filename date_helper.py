import argparse
from datetime import datetime


INPUT_DATE_FORMAT = "%Y-%m-%d"
RESPONSE_DATE_FORMAT = "%Y-%m-%dT00:00:00Z"
REQUEST_DATE_FORMAT = "%Y-%m-%dT00:00:00.000Z"


def format_date(date_object):
    date_formatted = datetime.strftime(date_object, RESPONSE_DATE_FORMAT)
    return date_formatted


def date_from_str(date_formatted):
    return datetime.strptime(date_formatted, RESPONSE_DATE_FORMAT)


def format_date_request(date_object):
    date_formatted = datetime.strftime(date_object, REQUEST_DATE_FORMAT)
    return date_formatted


def valid_date(s):
    try:
        return datetime.strptime(s, INPUT_DATE_FORMAT)
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)
