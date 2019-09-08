#!/usr/bin/env python3

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime, timedelta

import date_helper

from connection import Connection as Conn
from user_request import UserRequest


LOG = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s - %(process)s - %(levelname)s - %(message)s")
sh = logging.StreamHandler()
sh.setFormatter(formatter)
LOG.addHandler(sh)


async def crawl(request_str: str, only_available: bool, no_overall: bool, html: bool) -> None:
    availabilities = False
    user_requests = UserRequest.make_user_requests(request_str, only_available, no_overall, html)
    for res in asyncio.as_completed([x.process_request() for x in user_requests]):
        avail, out = await res
        availabilities = availabilities or avail
        print(out)

    return availabilities


async def crawl_info(request_str: str, html: bool) -> None:
    user_requests = UserRequest.make_user_requests(request_str, False, False, html)
    for res in asyncio.as_completed([x.get_camps_names() for x in user_requests]):
        print(await res)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd")
    parser_crawl = subparsers.add_parser("crawl")
    parser_crawl_info = subparsers.add_parser("crawl_info")

    for sub_parser in [parser_crawl, parser_crawl_info]:
        sub_parser.add_argument("--debug", "-d", action="store_true", help="Debug log level")
        sub_parser.add_argument(
            "--start-date", help="Start date [YYYY-MM-DD]", type=date_helper.valid_date
        )
        sub_parser.add_argument(
            "--end-date",
            help="End date [YYYY-MM-DD]. You expect to leave this day, not stay the night.",
            type=date_helper.valid_date,
        )
        sub_parser.add_argument(
            "--camps", dest="camps", metavar="camp", nargs="+", help="Camp ID(s)", type=str
        )
        sub_parser.add_argument(
            "--stdin",
            "-",
            action="store_true",
            help="Read list of camp ID(s) from stdin instead",
        )
        sub_parser.add_argument(
            "--request",
            help="Struct of requests as: start_date1..end_date1:id1,id2;start_date2..end_date2:id3,id4 \n" +
                "Dates should be in format YYYY-MM-DD. End date - you expect to leave this day, not stay the night"
        )
        sub_parser.add_argument(
            "--html",
            action="store_true",
            help="Print in html format",
        )
    parser_crawl.add_argument(
        "--only_available",
        action="store_true",
        help="Report only available sites",
    )
    parser_crawl.add_argument(
        "--no_overall",
        action="store_true",
        help="Do not print overall results line"
    )
    parser_crawl.add_argument(
        "--exit_code",
        action="store_true",
        help="Exit with code 0 if something is available, with 61 otherwise"
    )

    args = parser.parse_args()

    if args.debug:
        LOG.setLevel(logging.DEBUG)

    request = ""
    if args.request and args.camps:
        raise ValueError("You try to use request and camps methods both, you should chose one")
    if args.request:
        if args.start_date:
            LOG.warning("start_date does not make sense for the request")
        if args.end_date:
            LOG.warning("end_date does not make sense for the request")
        if args.stdin:
            LOG.warning("stdin option does not make sense for the request")
        request = args.request
    else:
        if args.stdin:
            camps = [p.strip() for p in sys.stdin]
        if not args.start_date:
            raise ValueError("start_date is not specified")
        if not args.end_date:
            raise ValueError("end_date is not specified")
        request = f"{args.start_date.date()}..{args.end_date.date()}:{','.join(camps)}"

    if args.cmd == "crawl":
        try:
            availabilities = asyncio.run(crawl(request, args.only_available, args.no_overall, args.html))
            if args.exit_code:
                sys.exit(0 if availabilities else 61)
        except Exception:
            print("Something went wrong")
            raise
    elif args.cmd == "crawl_info":
        asyncio.run(crawl_info(request, args.html))
    else:
        raise ValueError("Unknown command")
