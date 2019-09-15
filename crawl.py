#!/usr/bin/env python3

import asyncio
from user_request import UserRequest

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

