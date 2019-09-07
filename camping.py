#!/usr/bin/env python3

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime, timedelta

import requests
from fake_useragent import UserAgent


LOG = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s - %(process)s - %(levelname)s - %(message)s")
sh = logging.StreamHandler()
sh.setFormatter(formatter)
LOG.addHandler(sh)


BASE_URL = "https://www.recreation.gov"
AVAILABILITY_ENDPOINT = "/api/camps/availability/campground/"
MAIN_PAGE_ENDPOINT = "/api/camps/campgrounds/"

INPUT_DATE_FORMAT = "%Y-%m-%d"

SUCCESS_EMOJI = "🏕"
FAILURE_EMOJI = "❌"

headers = {"User-Agent": UserAgent().random}


def format_date(date_object):
    date_formatted = datetime.strftime(date_object, "%Y-%m-%dT00:00:00Z")
    return date_formatted


def generate_params(start, end):
    return {
        "start_date": format_date(start),
        "end_date": format_date(end)
    }


async def send_request(session, url, params):
    resp = session.get(url, params=params, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(
            "failedRequest",
            "ERROR, {} code received from {}: {}".format(
                resp.status_code, url, resp.text
            ),
        )
    return resp.json()


async def get_park_information(session, park_id, params):
    LOG.debug("Querying for {} with these params: {}".format(park_id, params))
    url = "{}{}{}".format(BASE_URL, AVAILABILITY_ENDPOINT, park_id)
    park_information = await send_request(session, url, params)
    LOG.debug(
        "Information for {}: {}".format(
            park_id, json.dumps(park_information, indent=1)
        )
    )

    return park_id, park_information


async def get_parks_information(session, park_ids, params):
    futures = {get_park_information(session, pid, params) for pid in park_ids}
    done, pending = await asyncio.wait(futures)
    return {r.result()[0]: r.result()[1] for r in done}


async def get_names_of_sites(session, park_ids):
    futures = {get_name_of_site(session, pid) for pid in park_ids}
    done, pending = await asyncio.wait(futures)
    return {r.result()[0]: r.result()[1] for r in done}


async def get_name_of_site(session, park_id):
    url = "{}{}{}".format(BASE_URL, MAIN_PAGE_ENDPOINT, park_id)
    resp = await send_request(session, url, {})
    return park_id, resp["campground"]["facility_name"]


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


async def _main(parks):
    out = []
    availabilities = False
    params = generate_params(args.start_date, args.end_date)

    session = requests.session()
    session.mount(
        'https://',
        requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=200,
            max_retries=3
        )
    )
    if not session:
        raise RuntimeError('Could not create session object')

    park_names_future = get_names_of_sites(session, parks)
    parks_infos_future = get_parks_information(session, parks, params)
    parks_infos = await parks_infos_future
    park_names = await park_names_future

    for park_id in parks:
        park_information = parks_infos[park_id]
        name_of_site = park_names[park_id]
        current, maximum = get_num_available_sites(
            park_information, args.start_date, args.end_date
        )
        if current:
            emoji = SUCCESS_EMOJI
            availabilities = True
        else:
            emoji = FAILURE_EMOJI

        if not args.only_available or current:
            out.append(
                "{} {} ({}): {} site(s) available out of {} site(s)".format(
                    emoji, name_of_site, park_id, current, maximum
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
        dest="parks", metavar="park", nargs="+", help="Park ID(s)", type=int
    )
    parser.add_argument(
        "--stdin",
        "-",
        action="store_true",
        help="Read list of park ID(s) from stdin instead",
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

    args = parser.parse_args()

    if args.debug:
        LOG.setLevel(logging.DEBUG)

    parks = args.parks or [p.strip() for p in sys.stdin]

    try:
        availabilities = asyncio.run(_main(parks))
        if args.exit_code:
            sys.exit(0 if availabilities else 61)
    except Exception:
        print("Something went wrong")
        raise
