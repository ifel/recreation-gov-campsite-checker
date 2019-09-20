import argparse
import json
import logging
from typing import List, Tuple, Optional

import date_helper
from connection import Connection

from datetime import timedelta, datetime as dt
from enum import Enum, auto


class UseType(Enum):
    Day = auto()
    Overnight = auto()

    @classmethod
    def validate(cls, v):
        if v == "":
            return None
        match = [x for x in cls if v.lower() == x.name.lower()]
        if match:
            return match[0]
        msg = "Not a valid date: '{0}'.".format(v)
        raise argparse.ArgumentTypeError(msg)

    @classmethod
    def all_names(cls):
        return [x.name for x in cls] + [""]


class UserRequest:
    SUCCESS_EMOJI = "🏕"
    FAILURE_EMOJI = "❌"

    def __init__(self, start_date: str, end_date: str, camp_ids: List[int],
                 only_available: bool, no_overall: bool, html: bool, skip_use_type: Optional[UseType]):
        self._conn: Connection = Connection(
            date_helper.valid_date(start_date),
            date_helper.valid_date(end_date)
        )
        self.start_date = start_date
        self._camp_ids: List[str] = camp_ids
        self._only_available = only_available
        self._no_overall = no_overall
        self._html = html
        self.available_at = dt.fromtimestamp(0)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._camp_names = {}
        self._skip_use_type = skip_use_type

    @classmethod
    def _make_user_request(cls, request_str: str, only_available: bool, no_overall: bool, html: bool, skip_use_type: Optional[UseType]): # -> UserRequest:
        dates, camp_ids_str = request_str.split(":")
        start_date, end_date = dates.split("..")
        camp_ids: List[int] = [int(x) for x in camp_ids_str.split(",")]
        return cls(start_date, end_date, camp_ids, only_available, no_overall, html, skip_use_type)

    @classmethod
    def make_user_requests(cls, requests_str: str, only_available: bool,
                           no_overall: bool, html: bool, skip_use_type: Optional[UseType]): # -> List[UserRequest]:
        ret: List[UserRequest] = []
        for request_str in requests_str.rstrip(";").split(";"):
            ret.append(cls._make_user_request(request_str, only_available, no_overall, html, skip_use_type))
        return ret

    def get_num_available_sites(self, resp):
        maximum = resp["count"]

        num_available = 0
        num_days = (self._conn.end_date - self._conn.start_date).days
        dates = [self._conn.end_date - timedelta(days=i) for i in range(1, num_days + 1)]
        dates = set(date_helper.format_date(i) for i in dates)
        for site in resp["campsites"].values():
            if self._skip_use_type and site['type_of_use'] == self._skip_use_type.name:
                continue
            available = bool(len(site["availabilities"]))
            for date, status in site["availabilities"].items():
                if date not in dates:
                    continue
                if status != "Available":
                    available = False
                    break
            if available:
                num_available += 1
                self._logger.debug("Available site {}: {}".format(num_available, json.dumps(site, indent=1)))
        if num_available > 0:
            self.available_at = dt.now()
        return num_available, maximum

    async def process_request(self) -> Tuple[bool, str]:
        out: List[str] = []
        availabilities: bool = False

        camp_names_future = self.camp_names()
        camps_infos_future = self._conn.get_camps_information(self._camp_ids)
        camps_infos = await camps_infos_future
        camps_names = await camp_names_future

        for camp_id in self._camp_ids:
            camp_information = camps_infos[camp_id]
            name_of_camp = camps_names[camp_id]
            current, maximum = self.get_num_available_sites(camp_information)
            if current:
                emoji = self.SUCCESS_EMOJI
                availabilities = True
            else:
                emoji = self.FAILURE_EMOJI

            if not self._only_available or current:
                if self._html:
                    out.append(
                        "- {} <a href=\"{}\">{}</a> ({}): {} site(s) available out of {} site(s)".format(
                            emoji,
                            self._conn.camp_availability_url(camp_id),
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

        result = ""
        if not self._no_overall:
            if availabilities:
                tmpl = "There are campsites available from {} to {}!!! \n"
            else:
                tmpl = "There are no campsites available from {} to {} :(\n"
            result = tmpl.format(
                        self._conn.start_date.strftime(date_helper.INPUT_DATE_FORMAT),
                        self._conn.end_date.strftime(date_helper.INPUT_DATE_FORMAT),
                    )
                
        result += "\n".join(out)
        if out:
            result += "\n"
        return availabilities, result

    async def get_camps_names(self) -> str:
        out = f"Looking for a place from {self._conn.start_date.date()} to {self._conn.end_date.date()} in:\n"
        camp_names = await self.camp_names()
        for camp_id, camp_name in camp_names.items():
            if self._html:
                out += f"- <a href=\"{self._conn.camp_url(camp_id)}\">{camp_name}</a> ({camp_id})\n"
            else:
                out += f"- {camp_name}\n"
        return out

    async def camp_names(self):
        if not self._camp_names:
            self._camp_names = await self._conn.get_camps_names(self._camp_ids)
        return self._camp_names