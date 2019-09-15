#!/usr/bin/env python3

import asyncio
import logging
import time
from datetime import timedelta, datetime as dt
from user_request import UserRequest


logger = logging.getLogger(__name__)

class Crawler:
    def __init__(self, request_str: str, only_available: bool, no_overall: bool, html: bool):
        self._user_requests = UserRequest.make_user_requests(request_str, only_available, no_overall, html)

    async def crawl_loop(self, check_freq, dont_recheck_avail_for) -> None:
        sleep_time: int
        await self.crawl_info()
        while True:
            availabilities = await self.crawl(dont_recheck_avail_for)
            sleep_time = check_freq
            logging.debug(f"Sleeping for {sleep_time} seconds before the next iteration")
            time.sleep(sleep_time)

    async def crawl(self, skip_avails_less_than: int = 15 * 60) -> None:
        availabilities = False
        threshold = dt.now() - timedelta(seconds=skip_avails_less_than)
        req_futures = [x.process_request() for x in self._user_requests if x.available_at < threshold]
        for res in asyncio.as_completed(req_futures):
            avail, out = await res
            availabilities = availabilities or avail
            print(out)

        return availabilities


    async def crawl_info(self) -> None:
        for res in asyncio.as_completed([x.get_camps_names() for x in self._user_requests]):
            print(await res)
