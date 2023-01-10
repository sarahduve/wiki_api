from wiki_api.client import WikiApiClient
from wiki_api.errors import WikiApiError

from typing import Tuple
from datetime import date

import pytest
import vcr

client = WikiApiClient()

@vcr.use_cassette('tests/vcr_cassettes/most_viewed_for_week.yml')
def test_get_most_viewed_for_week():
    response = client.get_most_viewed_for_week("20221218")
    assert isinstance(response, list)
    most_viewed = response[0]
    assert isinstance(response, list)
    assert isinstance(most_viewed, dict)
    assert set(["article", "views", "rank"]).issubset(most_viewed.keys())
    assert isinstance(most_viewed["article"], str)
    assert isinstance(most_viewed["views"], int)
    assert isinstance(most_viewed["rank"], int)

@vcr.use_cassette('tests/vcr_cassettes/most_viewed_for_month.yml')
def test_get_most_viewed_for_month():
    response = client.get_most_viewed_for_month(2022, 12)
    most_viewed = response[0]
    assert isinstance(response, list)
    assert isinstance(most_viewed, dict)
    assert set(["article", "views", "rank"]).issubset(most_viewed.keys())
    assert isinstance(most_viewed["article"], str)
    assert isinstance(most_viewed["views"], int)
    assert isinstance(most_viewed["rank"], int)

#  {'article': 'Pelé', 'views': 1165106, 'rank': 3}
@vcr.use_cassette('tests/vcr_cassettes/most_viewed_for_day.yml')
def test_get_most_viewed_for_day():
    response = client.get_most_viewed_for_day(2022, 12, 29)
    most_viewed = response[0]
    assert isinstance(response, list)
    assert isinstance(most_viewed, dict)
    assert set(["article", "views", "rank"]).issubset(most_viewed.keys())
    assert isinstance(most_viewed["article"], str)
    assert isinstance(most_viewed["views"], int)
    assert isinstance(most_viewed["rank"], int)

@vcr.use_cassette('tests/vcr_cassettes/article_views_for_week.yml')
def test_get_article_views_for_week():
    response = client.get_article_views_for_week("Pelé", "20221218")
    assert isinstance(response, int)

@vcr.use_cassette('tests/vcr_cassettes/article_views_for_month.yml')
def test_get_article_views_for_month():
    response = client.get_article_views_for_month("Lionel Messi", "20221201", "20221231")
    assert isinstance(response, int)

@vcr.use_cassette('tests/vcr_cassettes/most_article_views_in_month.yml')
def test_get_most_article_views_in_month():
    response = client.get_most_article_views_in_month("Pelé", 2022, 12)
    d, views = response
    assert isinstance(response, Tuple)
    assert isinstance(d, date)
    assert isinstance(views, int)


@vcr.use_cassette('tests/vcr_cassettes/most_article_views_in_week.yml')
def test_get_most_article_views_in_week():
    response = client.get_most_article_views_in_week("Kylian Mbappé", "20221218")
    d, views = response
    assert isinstance(response, Tuple)
    assert isinstance(d, date)
    assert isinstance(views, int)

@vcr.use_cassette('tests/vcr_cassettes/get_unavailable_data.yml')
def test_get_unavailable_data():
    with pytest.raises(WikiApiError) as excinfo:
        client.get_most_article_views_in_month("Pelé", 2015, 6)
    assert "we either do not have data for those date(s), or" in str(excinfo.value)

@vcr.use_cassette('tests/vcr_cassettes/check_week_math.yml')
def test_check_week_math():
    response = client.get_most_viewed_for_week("20221218")
    second_most_viewed_article = response[1]
    messi_views = client.get_article_views_for_week("Lionel Messi", "20221218")
    assert second_most_viewed_article["views"] == messi_views
    assert second_most_viewed_article["article"] == "Lionel_Messi"

@vcr.use_cassette('tests/vcr_cassettes/check_month_math.yml')
def test_check_month_math():
    response = client.get_most_viewed_for_month(2022, 12)
    third_most_viewed_article = response[2]
    world_cup_views = client.get_article_views_for_month("2022 FIFA World Cup", "20221201", "20221231")
    assert third_most_viewed_article["views"] == world_cup_views
    assert third_most_viewed_article["article"] == "2022_FIFA_World_Cup"
