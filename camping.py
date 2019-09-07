#!/usr/bin/env python3

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime, timedelta

from connection import Connection as Conn


LOG = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s - %(process)s - %(levelname)s - %(message)s")
sh = logging.StreamHandler()
sh.setFormatter(formatter)
LOG.addHandler(sh)


INPUT_DATE_FORMAT = "%Y-%m-%d"

SUCCESS_EMOJI = "🏕"
FAILURE_EMOJI = "❌"


def format_date(date_object):
    date_formatted = datetime.strftime(date_object, "%Y-%m-%dT00:00:00Z")
    return date_formatted


def generate_params(start, end):
    return {
        "start_date": format_date(start),
        "end_date": format_date(end)
    }


def get_num_available_sites(resp, start_date, end_date):
    maximum = resp["count"]

    num_available = 0
    num_days = (end_date - start_date).days
    dates = [end_date - timedelta(days=i) for i in range(1, num_days + 1)]
    dates = set(format_date(i) for i in dates)
    for site in resp["campsites"].values():
        available = bool(len(site["availabilities"]))
        for date, status in site["availabilities"].items():
            if date not in dates:
                continue
            if status != "Available":
                available = False
                break
        if available:
            num_available += 1
            LOG.debug("Available site {}: {}".format(num_available, json.dumps(site, indent=1)))
    return num_available, maximum


def valid_date(s):
    try:
        return datetime.strptime(s, INPUT_DATE_FORMAT)
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


async def _main(camps):
    out = []
    availabilities = False
    params = generate_params(args.start_date, args.end_date)

    camp_names_future = Conn.get_camps_names(camps)
    camps_infos_future = Conn.get_camps_information(camps, params)
    camps_infos = await camps_infos_future
    camps_names = await camp_names_future

    for camp_id in camps:
        camp_information = camps_infos[camp_id]
        name_of_camp = camps_names[camp_id]
        current, maximum = get_num_available_sites(
            camp_information, args.start_date, args.end_date
        )
        if current:
            emoji = SUCCESS_EMOJI
            availabilities = True
        else:
            emoji = FAILURE_EMOJI

        if not args.only_available or current:
            if args.html:
                out.append(
                    "- {} <a href=\"{}\">{}</a> ({}): {} site(s) available out of {} site(s)".format(
                        emoji,
                        Conn.camp_availability_url(camp_id),
                        name_of_camp,
                        camp_id,
                        current,
                        maximum
                    )
                )
            else:
                out.append(
                    "{} {} ({}): {} site(s) available out of {} site(s)".format(
                        emoji, name_of_camp, camp_id, current, maximum
                    )
                )

    if not args.no_overall:
        if availabilities:
            print(
                "There are campsites available from {} to {}!!!".format(
                    args.start_date.strftime(INPUT_DATE_FORMAT),
                    args.end_date.strftime(INPUT_DATE_FORMAT),
                )
            )
        else:
            print("There are no campsites available :(")
    print("\n".join(out))
    return availabilities


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", "-d", action="store_true", help="Debug log level")
    parser.add_argument(
        "--start-date", required=True, help="Start date [YYYY-MM-DD]", type=valid_date
    )
    parser.add_argument(
        "--end-date",
        required=True,
        help="End date [YYYY-MM-DD]. You expect to leave this day, not stay the night.",
        type=valid_date,
    )
    parser.add_argument(
        dest="camps", metavar="camp", nargs="+", help="Camp ID(s)", type=int
    )
    parser.add_argument(
        "--stdin",
        "-",
        action="store_true",
        help="Read list of camp ID(s) from stdin instead",
    )
    parser.add_argument(
        "--only_available",
        action="store_true",
        help="Report only available sites",
    )
    parser.add_argument(
        "--no_overall",
        action="store_true",
        help="Do not print overall results line"
    )
    parser.add_argument(
        "--exit_code",
        action="store_true",
        help="Exit with code 0 if something is available, with 61 otherwise"
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Print in html format",
    )

    args = parser.parse_args()

    if args.debug:
        LOG.setLevel(logging.DEBUG)

    camps = args.camps or [p.strip() for p in sys.stdin]

    try:
        availabilities = asyncio.run(_main(camps))
        if args.exit_code:
            sys.exit(0 if availabilities else 61)
    except Exception:
        print("Something went wrong")
        raise
