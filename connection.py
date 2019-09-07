import asyncio
import json
import logging
import requests
from fake_useragent import UserAgent


logger = logging.getLogger(__name__)


class Connection:
    SESSION = None
    HEADERS = {
        "User-Agent": UserAgent().random,
        'Accept-Encoding': 'identity, deflate, compress, gzip'
    }
    BASE_URL = "https://www.recreation.gov"
    AVAILABILITY_ENDPOINT = "/api/camps/availability/campground/"
    MAIN_PAGE_ENDPOINT = "/api/camps/campgrounds/"

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
    async def get_park_information(cls, park_id, params):
        logger.debug("Querying for {} with these params: {}".format(park_id, params))
        url = "{}{}{}".format(cls.BASE_URL, cls.AVAILABILITY_ENDPOINT, park_id)
        park_information = await cls.send_request(url, params)
        logger.debug(
            "Information for {}: {}".format(
                park_id, json.dumps(park_information, indent=1)
            )
        )

        return park_id, park_information

    @classmethod
    async def get_parks_information(cls, park_ids, params):
        futures = {cls.get_park_information(pid, params) for pid in park_ids}
        done, pending = await asyncio.wait(futures)
        return {r.result()[0]: r.result()[1] for r in done}

    @classmethod
    async def get_names_of_sites(cls, park_ids):
        futures = {cls.get_name_of_site(pid) for pid in park_ids}
        done, pending = await asyncio.wait(futures)
        return {r.result()[0]: r.result()[1] for r in done}

    @classmethod
    async def get_name_of_site(cls, park_id):
        url = "{}{}{}".format(cls.BASE_URL, cls.MAIN_PAGE_ENDPOINT, park_id)
        resp = await cls.send_request(url, {})
        return park_id, resp["campground"]["facility_name"]
