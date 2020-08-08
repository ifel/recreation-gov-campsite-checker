import asyncio
import copy
from dateutil.relativedelta import relativedelta
import json
import logging
import os
import requests
from fake_useragent import UserAgent

import date_helper


class Connection:
    SESSION = None
    HEADERS = {
        "User-Agent": UserAgent().random,
        'Accept-Encoding': 'identity, deflate, compress, gzip'
    }
    BASE_URL = "https://www.recreation.gov"
    AVAILABILITY_ENDPOINT = "api/camps/availability/campground/"
    MAIN_PAGE_ENDPOINT = "api/camps/campgrounds/"
    CAMP_NAMES = {}
    CAMP_RATES = {}

    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self._logger = logging.getLogger(self.__class__.__name__)

    @classmethod
    def get_session(cls):
        if not cls.SESSION:
            cls.SESSION = requests.session()
            if not cls.SESSION:
                raise RuntimeError('Could not create session object')
            cls.SESSION.mount(
                'https://',
                requests.adapters.HTTPAdapter(
                    pool_connections=10,
                    pool_maxsize=200,
                    max_retries=3
                )
            )
        return cls.SESSION

    @classmethod
    async def send_request(cls, url, params):
        resp = cls.get_session().get(url, params=params, headers=cls.HEADERS)
        if resp.status_code != 200:
            raise RuntimeError(
                "failedRequest",
                "ERROR, {} code received from {}: {}".format(
                    resp.status_code, url, resp.text
                ),
            )
        return resp.json()

    @classmethod
    def _api_camp_url(cls, camp_id):
        return os.path.join(cls.BASE_URL, cls.MAIN_PAGE_ENDPOINT, str(camp_id))

    @classmethod
    def _camp_rates_url(cls, camp_id):
        return os.path.join(cls._api_camp_url(camp_id), "rates")

    @classmethod
    def _camp_avail_url(cls, camp_id, month_date):
        return os.path.join(cls.BASE_URL, cls.AVAILABILITY_ENDPOINT, str(camp_id), "month")

    def diff_month(self, start_date, end_date):
        return (end_date.year - start_date.year) * 12 + end_date.month - start_date.month

    async def get_camp_information_month(self, camp_id, month_date):
        request_params = {
            "start_date": date_helper.format_date_request(month_date),
        }
        self._logger.debug(
            f"Querying for {camp_id} with these params: {request_params}")
        camp_information = await self.send_request(
            self._camp_avail_url(camp_id, month_date), request_params
        )
        return camp_information

    async def get_camp_information(self, camp_id):
        months = self.diff_month(self.start_date, self.end_date) + 1
        tasks = []
        for i in range(months):
            start_of_month = (self.start_date +
                              relativedelta(months=i)).replace(day=1)
            tasks.append(asyncio.create_task(
                self.get_camp_information_month(camp_id, start_of_month)))
        infos = await asyncio.gather(*tasks)
        camp_information = {}
        for info in infos:
            if not camp_information:
                camp_information = copy.deepcopy(info)
                continue
            for campsite_id, campsite_infos in info["campsites"].items():
                if campsite_id not in camp_information["campsites"]:
                    camp_information["campsites"][campsite_id] = campsite_infos
                else:
                    camp_information["campsites"][campsite_id]["availabilities"].update(
                        campsite_infos["availabilities"])
        camp_information["count"] = len(camp_information["campsites"])
        self._logger.debug(
            "Information for {}: {}".format(
                camp_id, json.dumps(camp_information, indent=1)
            )
        )

        return camp_id, camp_information

    async def get_camps_information(self, camp_ids):
        futures = {self.get_camp_information(pid) for pid in camp_ids}
        done, pending = await asyncio.wait(futures)
        return {r.result()[0]: r.result()[1] for r in done}

    async def get_camp_rates(self, camp_id):
        if camp_id not in self.CAMP_RATES.keys():
            self.CAMP_RATES[camp_id] = await self.send_request(
                self._camp_rates_url(camp_id), {})
        return self.CAMP_RATES[camp_id]

    @classmethod
    async def get_camps_names(cls, camp_ids):
        futures = {cls.get_camp_name(pid) for pid in camp_ids}
        done, pending = await asyncio.wait(futures)
        return {r.result()[0]: r.result()[1] for r in done}

    @classmethod
    async def get_camp_name(cls, camp_id):
        if camp_id not in cls.CAMP_NAMES:
            resp = await cls.send_request(cls._api_camp_url(camp_id), {})
            cls.CAMP_NAMES[camp_id] = resp["campground"]["facility_name"]
        return camp_id, cls.CAMP_NAMES[camp_id]

    @classmethod
    def campsite_url(cls, camp_id):
        return os.path.join(cls.BASE_URL, f"camping/campsites/{camp_id}/")

    @classmethod
    def camp_url(cls, camp_id):
        return os.path.join(cls.BASE_URL, f"camping/campgrounds/{camp_id}/")

    @classmethod
    def camp_availability_url(cls, camp_id):
        return os.path.join(cls.camp_url(camp_id), "availability")
