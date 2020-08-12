#!/usr/bin/env python3

import asyncio
import datetime
import logging
import os
import time
import tempfile

from typing import List, Optional

import telegram_send
from user_request import UserRequest, UseType, CampsiteType


class Crawler:
    def __init__(self, request_str: str, only_available: bool, no_overall: bool, html: bool,
                 telegram_token: str, telegram_chat_id: str, skip_use_type: Optional[UseType],
                 skip_campsite_types: Optional[CampsiteType]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._user_requests = UserRequest.make_user_requests(
            request_str, only_available, no_overall, html, skip_use_type, skip_campsite_types)
        self._telegram_config: str = self._gen_telegram_config(
            telegram_token, telegram_chat_id)
        self._telegram_html = html
        self._sent_into_at = datetime.datetime.fromtimestamp(0)

    async def crawl_loop(self, check_freq, dont_recheck_avail_for, send_info_every) -> None:
        sleep_time: int
        while True:
            start_time = datetime.datetime.now()
            if self._sent_into_at < datetime.datetime.now() - datetime.timedelta(hours=send_info_every):
                self._logger.info("Time to get search info")
                await self.crawl_info()
                self._sent_into_at = datetime.datetime.now()
            self._logger.info("Getting availabilities")
            availabilities = await self.crawl(dont_recheck_avail_for)
            sleep_time = check_freq
            end_time = datetime.datetime.now()
            time_diff = end_time - start_time
            self._logger.debug(
                f"Crawler loop took {time_diff.seconds}.{time_diff.microseconds} seconds")
            self._logger.debug(
                f"Sleeping for {sleep_time} seconds before the next iteration")
            time.sleep(sleep_time)

    async def crawl(self, skip_avails_less_than: int = 15 * 60) -> None:
        availabilities = False
        threshold = datetime.datetime.now() - datetime.timedelta(seconds=skip_avails_less_than)
        requests_above_threshold = [
            x for x in self._user_requests_in_future() if x.available_at < threshold]
        futures = [x.process_request() for x in sorted(
            requests_above_threshold, key=lambda us: us.start_date)]
        self._logger.debug(
            f"Getting availability for {len(futures)} user requests")
        all_out: str = ""
        for avail, out in await asyncio.gather(*futures):
            availabilities = availabilities or avail
            all_out += out
        if availabilities:
            await self._send_to_telegram_or_print(all_out)
        self._logger.info(all_out)

        return availabilities

    async def crawl_info(self) -> None:
        info: str = ""
        futures = [x.get_camps_names() for x in sorted(
            self._user_requests_in_future(), key=lambda us: us.start_date)]
        for res in await asyncio.gather(*futures):
            info += res
        self._logger.info(info)
        await self._send_to_telegram_or_print(info)

    def _user_requests_in_future(self) -> List[UserRequest]:
        tomorrow = datetime.datetime.combine(
            datetime.date.today() + datetime.timedelta(days=1),
            datetime.datetime.min.time()
        )
        return [x for x in self._user_requests if datetime.datetime.strptime(x.start_date, '%Y-%m-%d') >= tomorrow]

    def _gen_telegram_config(self, token, chat_id) -> str:
        tmp_path: str = ""
        if token and chat_id:
            self._logger.info("Generating telegram config")
            tmp_handle, tmp_path = tempfile.mkstemp()
            with os.fdopen(tmp_handle, 'w') as fh:
                print(
                    f"[telegram]\ntoken = {token}\nchat_id = {chat_id}\n", file=fh)
        return tmp_path

    async def _send_to_telegram_or_print(self, message: str):
        if self._telegram_config:
            self._logger.debug("Sending a message to telegram chat")
            telegram_send.send(
                messages=[message],
                conf=self._telegram_config,
                parse_mode="html" if self._telegram_html else "text"
            )
        else:
            print(message)
