import asyncio
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


class CampsiteType(Enum):
    STANDARD_NONELECTRIC = auto()
    STANDARD_ELECTRIC = auto()
    TENT_ONLY_NONELECTRIC = auto()
    CABIN_NONELECTRIC = auto()
    CABIN_ELECTRIC = auto()

    MANAGEMENT = auto()
    WALK_TO = auto()
    RV_NONELECTRIC = auto()
    GROUP_SHELTER_NONELECTRIC = auto()
    GROUP_HIKE_TO = auto()
    HIKE_TO = auto()
    GROUP_STANDARD_NONELECTRIC = auto()
    BOAT_IN = auto()
    EQUESTRIAN_NONELECTRIC = auto()

    @classmethod
    def validate_multi(cls, v):
        if v == "":
            return None
        values = [x.strip().replace(" ", "_") for x in v.split(",")]
        return [cls.validate(x) for x in values]

    @classmethod
    def validate(cls, v):
        match = [x for x in cls if v.lower() == x.name.lower()]
        if match:
            return match[0]
        msg = "Not a valid date: '{0}'.".format(v)
        raise argparse.ArgumentTypeError(msg)

    @classmethod
    def all_names(cls):
        return [x.name for x in cls] + [""]


class CampsiteInfo:
    @classmethod
    async def create(cls, campsite_id, capacity_rating, min_num_people, max_num_people, loop, site, campsite_type, conn, camp_id):
        myself = cls()
        myself._logger = logging.getLogger(cls.__class__.__name__)
        myself.campsite_id = campsite_id
        myself.capacity_rating = capacity_rating
        myself.min_num_people = min_num_people
        myself.max_num_people = max_num_people
        myself.loop = loop
        myself.site = site
        myself.campsite_type = campsite_type
        myself.rate, myself.rate_str = await myself.get_rate(await conn.get_camp_rates(camp_id), conn.start_date, conn.end_date)
        return myself

    async def get_rate(self, rates, start_date, end_date):
        rate = {}
        ret = (0, "NaN")
        # look for the rate structiure
        for r in rates['rates_list']:
            season_start = dt.strptime(r['season_start'], '%Y-%m-%dT00:00:00Z')
            season_end = dt.strptime(r['season_end'], '%Y-%m-%dT00:00:00Z')
            if start_date >= season_start and end_date <= season_end:
                rate = r
                break
        if not rate:
            self._logger.warning("Could not find rate")
            return ret

        key = None
        for k, v in rate["site_type_map"].items():
            if v == self.campsite_type:
                key = k
                break
        else:
            self._logger.warning("Could not find rate key")
            return ret

        # There are more values, never seen them non 0/none for what I'm looking for
        s = rate["rate_map"][key]
        if s["per_night"]:
            ret = (s["per_night"], f"${s['per_night']}/night")
        elif s["per_person"]:
            ret = (s["per_person"], f"${s['per_person']}/person")
        elif s["group_fees"]:
            k = list(s["group_fees"].keys())[0]
            v = s["group_fees"][k]
            ret = (v, f"${v}/group {k}")
        if not ret[0]:
            self._logger.warning("Could not find rate")
        return ret

    def __str__(self):
        return f"  - \"{self.loop}\" - {self.site}, {self.capacity_rating} {self.min_num_people}-{self.max_num_people} ppl, {self.rate_str}"

    def html(self):
        url = Connection.campsite_url(self.campsite_id)
        return f"  - <a href=\"{url}\">\"{self.loop}\" - {self.site}</a>, {self.capacity_rating} {self.min_num_people}-{self.max_num_people} ppl, {self.rate_str}"


class UserRequest:
    SUCCESS_EMOJI = "🏕"
    FAILURE_EMOJI = "❌"
    SITE_INFO_THRESHOLD = 5

    def __init__(self, start_date: str, end_date: str, camp_ids: List[int],
                 only_available: bool, no_overall: bool, html: bool, skip_use_type: Optional[UseType],
                 skip_campsite_types: Optional[CampsiteType]):
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
        self._skip_campsite_types_names: List[str] = [
            x.name.upper() for x in skip_campsite_types] if skip_use_type else []

    @classmethod
    def _make_user_request(cls, request_str: str, only_available: bool, no_overall: bool, html: bool,
                           skip_use_type: Optional[UseType], skip_campsite_types: Optional[CampsiteType]):  # -> UserRequest:
        dates, camp_ids_str = request_str.split(":")
        start_date, end_date = dates.split("..")
        camp_ids: List[int] = [int(x) for x in camp_ids_str.split(",")]
        return cls(start_date, end_date, camp_ids, only_available, no_overall, html, skip_use_type, skip_campsite_types)

    @classmethod
    def make_user_requests(cls, requests_str: str, only_available: bool,
                           no_overall: bool, html: bool, skip_use_type: Optional[UseType],
                           skip_campsite_types: Optional[CampsiteType]):  # -> List[UserRequest]:
        ret: List[UserRequest] = []
        for request_str in requests_str.rstrip(";").split(";"):
            ret.append(cls._make_user_request(request_str, only_available,
                                              no_overall, html, skip_use_type, skip_campsite_types))
        return ret

    async def get_available_sites_info(self, resp, camp_id):
        maximum = resp["count"]

        available_sites_info: List[CampsiteInfo] = []
        num_days = (self._conn.end_date - self._conn.start_date).days
        dates = {self._conn.end_date - timedelta(days=i) for i in range(num_days)}
        for site in resp["campsites"].values():
            if self._skip_use_type and site['type_of_use'] == self._skip_use_type.name:
                continue
            if site["campsite_type"].upper().replace(" ", "_") in self._skip_campsite_types_names:
                continue
            available_dates = {date_helper.date_from_str(
                date) for date, status in site["availabilities"].items() if status == "Available"}
            if dates.issubset(available_dates):
                available_sites_info.append(
                    await CampsiteInfo.create(
                        site["campsite_id"],
                        site["capacity_rating"],
                        site["min_num_people"],
                        site["max_num_people"],
                        site["loop"],
                        site["site"],
                        site["campsite_type"],
                        self._conn,
                        camp_id
                    )
                )
                self._logger.debug("Available site #{}: {}".format(
                    len(available_sites_info), json.dumps(site, indent=1)))
        if available_sites_info:
            self.available_at = dt.now()
        return maximum, available_sites_info

    def _process_site_availability(self, available_sites_info: List[CampsiteInfo],
                                   camp_id: int, name_of_camp: str, sites_num: int) -> List[str]:
        """ Process available_sites_info and returns list of lines ready to be printed. """
        ret: List[str] = []
        num_available = len(available_sites_info)
        if available_sites_info:
            emoji = self.SUCCESS_EMOJI
            availabilities = True
        else:
            emoji = self.FAILURE_EMOJI

        if not self._only_available or available_sites_info:
            avg_pr = ":"
            if num_available > self.SITE_INFO_THRESHOLD:
                avg_pr = f", avg price: ${sum([x.rate for x in available_sites_info if x.rate > 0])/num_available}"
            if self._html:
                ret.append(
                    "- {} <a href=\"{}\">{}</a> ({}): {} site(s) available out of {} site(s){}".format(
                        emoji,
                        self._conn.camp_availability_url(camp_id),
                        name_of_camp,
                        camp_id,
                        num_available,
                        sites_num,
                        avg_pr
                    )
                )
                if num_available <= self.SITE_INFO_THRESHOLD:
                    for site_info in available_sites_info:
                        ret.append(site_info.html())
            else:
                ret.append(
                    "{} {} ({}): {} site(s) available out of {} site(s){}".format(
                        emoji, name_of_camp, camp_id, num_available, sites_num, avg_pr
                    )
                )
                if num_available <= self.SITE_INFO_THRESHOLD:
                    for site_info in available_sites_info:
                        ret.append(str(site_info))
        return ret

    async def process_request(self) -> Tuple[bool, str]:
        out: List[str] = []
        camps_infos, camps_names = await asyncio.gather(
            *[
                self._conn.get_camps_information(self._camp_ids),
                self.camp_names()
            ]
        )

        for camp_id in self._camp_ids:
            camp_information = camps_infos[camp_id]
            name_of_camp = camps_names[camp_id]
            # TODO antipattern, but it's cached
            sites_num, available_sites_info = await self.get_available_sites_info(camp_information, camp_id)
            out.extend(
                self._process_site_availability(
                    available_sites_info, camp_id, name_of_camp, sites_num))

        result = ""
        availabilities: bool = bool(out)
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
