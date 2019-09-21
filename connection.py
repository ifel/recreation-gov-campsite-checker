import asyncio
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
        self._request_params = None
        self._logger = logging.getLogger(self.__class__.__name__)

    @property
    def request_params(self):
        if not self._request_params:
            self._request_params = {
                "start_date": date_helper.format_date(self.start_date),
                "end_date": date_helper.format_date(self.end_date)
            }
        return self._request_params

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
    def _camp_avail_url(cls, camp_id):
        return os.path.join(cls.BASE_URL, cls.AVAILABILITY_ENDPOINT, str(camp_id))

    async def get_camp_information(self, camp_id):
        self._logger.debug("Querying for {} with these params: {}".format(
            camp_id, self.request_params))
        camp_information = await self.send_request(
            self._camp_avail_url(camp_id), self.request_params)
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
