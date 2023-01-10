from wiki_api.errors import WikiApiError
import pdb

from calendar import monthrange
from collections import Counter
from datetime import datetime, timedelta, date
from typing import Tuple
from urllib.parse import urlencode
import json

import requests
from requests.utils import quote

class WikiApiClient:

    def __init__(self, user_agent="Sarah Duve <info@example.com>",
                 hostname="wikimedia.org", version="rest_v1",
                 project="en.wikipedia.org", access="all-access",
                 agent="user", error_class=WikiApiError):

        """
        Create a WikiApiClient

        Args:
            user_agent (str, optional): User-Agent string to use for HTTP requests. Should be
                                        something that allows you to be contacted if
                                        need be, see https://www.mediawiki.org/wiki/REST_API
            hostname (str, optional):   Hostname of API being accessed
            version (str, optional):    Version of API being accessed
            project (str, optional):    The domain of any Wikimedia project, for example
                                        'en.wikipedia.org', 'www.mediawiki.org' or 'commons.wikimedia.org'.
            access (str, optional):     If you want to filter by access method, use one
                                        of 'desktop', 'mobile-app' or 'mobile-web'. If you are
                                        interested in pageviews regardless of access method,
                                        use 'all-access'.
            agent (str, optional):      If you want to filter by agent type, use one of 'user',
                                        'automated' or 'spider'. If you are interested in pageviews
                                        regardless of agent type, use 'all-agents'.

        Returns:
            WikiApiClient:    A new instance of the WikiApiClient class.
        """


        self._session = requests.session()
        self._headers = {"User-Agent": user_agent}
        self._project = project
        self._access = access
        self._agent = agent
        self._url = f"https://{hostname}/api/{version}/metrics"
        self._error_class = error_class

    def _return_response(self, response):
        """
        If response is OK, returns the JSON. if it's not, raises an error
        based on the error_class

        Args:
            response (requests.Response): The response from an HTTP request:

        Returns:
            str: JSON string
        """

        try:
            if not response.ok:
                try:
                    data = response.json()
                except ValueError:
                    data = response.data
                raise self._error_class(status_code=response.status_code, **data)
            if response and response.text:
                return response.text
        except:
            print(f'ERROR while fetching {data["uri"]}')
            raise


    def _get_api_url(self, endpoint, article=None, granularity=None, start=None, end=None):
        """
        Constructs full API url

        Args:
            endpoint (str):              The endpoint being accessed. Currently "/pageviews/per-article" or
                                         "/pageviews/top" have supporting methods
            article (str, optional):     The article to fetch pageviews for, if applicable.
                                         Must already be URI-encoded and have spaces replaced with
                                         underscores
            granularity (str, optional): For `per-article` endpoints, the granularity of the data to be
                                         returned: "daily" or "monthly"
            start (date, optional):  Date object representing beginning of reporting window
            end (date, optional):    Date object representing end of reporting window

        Returns:
            str: Full URL ready to be fetched/hit
        """

        full_url = f"{self._url}{endpoint}/{self._project}/{self._access}"
        if article:
            start = start.strftime('%Y%m%d')
            end = end.strftime('%Y%m%d')
            full_url += f"/{self._agent}/{article}/{granularity}/{start}/{end}"
        return full_url

    def _get(self, full_url):
        """
        Wrapper around requests `.get()` method, using the WikiAPIClient instance's session and headers

        Args:
            full_url(str): Full URL to GET

        Returns:
            str: JSON string
        """

        response = self._session.get(full_url, headers=self._headers)
        return self._return_response(response)

    def _encode_article(self, article):
        """
        Converts user supplied article name to format needed by API

        Args:
            article (str): User supplied "article"

        Returns:
            str: Encoded "article" string

        """

        #  article = article.capitalize()
        article = article.replace(' ', '_')
        article_safe = quote(article, safe='')
        return article_safe

    def get_most_viewed_for_week(self, start_date, limit=999):
        """
        Get a list of the most viewed Wikipedia articles for a rolling week (any 7 day period) starting
        with `start_date`.

        Args:
            start_date (str): A string representing a date in the format `YYYYMMDD`, where
                             `YYYY` is the four-digit year, `MM` is the two-digit month, and
                             `DD` is the two-digit day of the month.
            limit (int, optional): Number of articles to return. Defaults to 999 to return 1000 articles.

        Returns:
            list: A sorted list of article dicts: [
                {
                    article: <str>,
                    views: <int>,
                    rank: <int>,
                }
                ...
            ]
        """

        # error anything before 20150701
        week_start = datetime.strptime(start_date, '%Y%m%d')
        week_end = week_start + timedelta(days=6)
        counter = Counter()

        while week_start <= week_end:
            articles = self.get_most_viewed_for_day(week_start.year,
                                                    week_start.month,
                                                    week_start.day)

            for article in articles:
                counter.update({article["article"]: article["views"]})
            week_start += timedelta(days=1)

        result = [{'article': article, 'views': views, 'rank': rank}
                  for rank, (article, views) in enumerate(counter.items(), start=1)][:limit]

        return result

    def get_most_viewed_for_month(self, year, month, limit=999):
        """
        Get a list of the most viewed Wikipedia articles for a given month.

        Args:
            year (int):  Year to be fetched
            month (int): An integer representing the month to fetch, where 1
                         represents January, 2 represents February, and so on.
            limit (int, optional): Number of articles to return. Defaults to 999 to return 1000 articles.

        Returns:
            list: A sorted list of article dicts: [
                {
                    article: <str>,
                    views: <int>,
                    rank: <int>,
                }
                ...
            ]
        """

        month = date(year, month, 1)
        url = (self._get_api_url("/pageviews/top") +
                               f"/{month.year}/{month.month}/all-days")

        return json.loads(self._get(url))["items"][0]["articles"][:limit]

    def get_most_viewed_for_day(self, year, month, day):
        """
        Get a list of the most viewed Wikipedia articles for a given day.

        Args:
            year (int):  Year to be fetched
            month (int): An integer representing the month to fetch, where 1
                         represents January, 2 represents February, and so on.
            day (int): Day to be fetched

        Returns:
            list: A sorted list of article dicts: [
                {
                    article: <str>,
                    views: <int>,
                    rank: <int>,
                }
                ...
            ]
        """

        month = str(month).zfill(2)
        day = str(day).zfill(2)

        url = (self._get_api_url("/pageviews/top") +
                                f"/{year}/{month}/{day}")

        articles = json.loads(self._get(url))["items"][0]["articles"]

        return articles

    def get_article_views_for_week(self, article, start_date):
        """
        Get a given article's total views for a rolling week (7 day period starting with `start_date`)

        Args:
            article (str):    Article to fetch pageviews for
            start_date (str): A string representing a date in the format `YYYYMMDD`, where
                             `YYYY` is the four-digit year, `MM` is the two-digit month, and
                             `DD` is the two-digit day of the month.
        Returns:
            int: total article pageviews for given 1 week period

        """

        article = self._encode_article(article)
        week_start = datetime.strptime(start_date, '%Y%m%d')
        week_end = week_start + timedelta(days=6)

        url = self._get_api_url("/pageviews/per-article", article=article,
                                granularity="daily", start=week_start, end=week_end)
        daily_views = json.loads(self._get(url))["items"]

        return sum(day["views"] for day in daily_views)

    def get_article_views_for_month(self, article, start_date, end_date):
        """
        Get an article's total views for a given month

        Args:
            article (str): Article to fetch pageviews for
            start_date (str): A string representing a date in the format `YYYYMMDD`, where
                              `YYYY` is the four-digit year, `MM` is the two-digit month, and
                              `DD` is the two-digit day of the month. Must be first day of the
                              particular month.
            end_date (str): A string representing a date in the format `YYYYMMDD`, where
                              `YYYY` is the four-digit year, `MM` is the two-digit month, and
                              `DD` is the two-digit day of the month. Must be last day of the
                              particular month, including leap days.
        Returns:
            int: total article pageviews for given month

        """

        article = self._encode_article(article)
        start_date = datetime.strptime(start_date, '%Y%m%d')
        end_date = datetime.strptime(end_date, '%Y%m%d')

        url = self._get_api_url("/pageviews/per-article", article=article,
                                granularity="monthly", start=start_date, end=end_date)
        monthly_views = json.loads(self._get(url))["items"]
        return monthly_views[0]["views"]

    def _get_pageviews(self, article, start_date, end_date):
        """
        Given a particular date range, get the day a given article had the most pageviews

        Args:
            article (str):              Article to fetch pageviews for
            start_date (date):      Date object representing beginning of reporting window
            end_date (date):        Date object representing end of reporting window, inclusive

        Returns:
            Tuple[datetime, int]:       A tuple containing a datetime object
                                        representing the date with the most pageviews in
                                        the given period, and an integer representing the
                                        number of pageviews

        """

        url = self._get_api_url("/pageviews/per-article", article=article,
                                granularity="daily", start=start_date, end=end_date)

        daily_views = json.loads(self._get(url))["items"]
        most_views = sorted(daily_views, key=lambda x: x["views"], reverse=True)[0]
        return (datetime.strptime(most_views["timestamp"], '%Y%j%H%M'), most_views["views"])

    def get_most_article_views_in_month(self, article, year, month):
        """
        Get the day a particular article had the most pageviews in a given month

        Args:
            article (str):  Article to fetch pageviews for
            year (int):     An integer representing the year to fetch
            month (int):    An integer representing the month to fetch, where 1
                            represents January, 2 represents February, and so on.

        Returns:
             Tuple[datetime, int]:  A tuple containing a datetime object
                                    representing the date with the most pageviews in
                                    the given month, and an integer representing the
                                    number of pageviews

        """
        article = self._encode_article(article)

        start = date(year, month, 1)
        _ , end = monthrange(year, month)
        end = date(year, month, end)

        return self._get_pageviews(article, start, end)

    def get_most_article_views_in_week(self, article, start_date):
        """
        Get the day a particular article had the most pageviews in the rolling week
        (any 7 day period) starting with `start_date`

        Args:
            article (str):      Article to fetch pageviews for
            start_date (str):   A string representing a date in the format `YYYYMMDD`, where
                                `YYYY` is the four-digit year, `MM` is the two-digit month, and
                                `DD` is the two-digit day of the month.
        Returns:
            Tuple[datetime, int]:   A tuple containing a `datetime` object
                                    representing the date with the most pageviews in
                                    the given period, and an integer representing the
                                    number of pageviews

        """

        article = self._encode_article(article)

        start = datetime.strptime(start_date, '%Y%m%d')
        end = start + timedelta(days=6)

        return self._get_pageviews(article, start, end)
