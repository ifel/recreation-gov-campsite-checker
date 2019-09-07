#!/usr/bin/env python3

import asyncio
import argparse
import sys
from connection import Connection as Conn

async def _main(camps, html):
    camp_names = await Conn.get_camps_names(camps)
    for camp_id in camps:
        camp_name = camp_names[camp_id]
        if html:
            print(f"- <a href=\"{Conn.camp_url(camp_id)}\">{camp_name}</a> ({camp_id})")
        else:
            print(f"- {camp_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
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
        "--html",
        action="store_true",
        help="Print in html format",
    )
    args = parser.parse_args()

    camps = args.camps or [p.strip() for p in sys.stdin]
    
    if not camps:
        sys.exit(61)
    
    asyncio.run(_main(camps, args.html))
    sys.exit(0)