#!/usr/bin/env python3

import asyncio
import logging
import os
import time
import tempfile
from datetime import timedelta, datetime as dt

import telegram_send
from user_request import UserRequest


logger = logging.getLogger(__name__)

class Crawler:
    def __init__(self, request_str: str, only_available: bool, no_overall: bool, html: bool,
                 telegram_token: str, telegram_chat_id: str):
        self._user_requests = UserRequest.make_user_requests(request_str, only_available, no_overall, html)
        self._telegram_config: str = self._gen_telegram_config(telegram_token, telegram_chat_id)
        self._telegram_html = html

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
        all_out: str = ""
        for res in asyncio.as_completed(req_futures):
            avail, out = await res
            availabilities = availabilities or avail
            print(out)
            all_out += out
        if availabilities:
            await self._telegram_send(all_out)

        return availabilities

    async def crawl_info(self) -> None:
        info: str = ""
        for res in asyncio.as_completed([x.get_camps_names() for x in self._user_requests]):
            info += await res
        print(info)
        await self._telegram_send(info)

    def _gen_telegram_config(self, token, chat_id) -> str:
        tmp_path: str = ""
        if token and chat_id:
            tmp_handle, tmp_path = tempfile.mkstemp()
            with os.fdopen(tmp_handle, 'w') as fh:
               print(f"[telegram]\ntoken = {token}\nchat_id = {chat_id}\n", file=fh)
        return tmp_path

    async def _telegram_send(self, message: str):
        if self._telegram_config:
            telegram_send.send(
                messages=[message],
                conf=self._telegram_config,
                parse_mode="html" if self._telegram_html else "text"
            )