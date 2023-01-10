# wiki_api
A Python wrapper for the Wikipedia REST API

## Set up
I used pipenv for this project, but for your convenience, there is also a requirements.txt file, so you can use either to install dependencies.

#### pipenv
```
$ pipenv install
```
#### pip
```
$ python -m pip install -r requirements.txt
```

## Usage

```
from wiki_api.client import WikiApiClient
client = WikiApiClient(user_agent="Your Name <your_email@example.com>)

# Retrieve a list of the most viewed articles for a week or a month
client.get_most_viewed_for_week("20221218")
client.get_most_viewed_for_month(2022, 12)
client.get_most_viewed_for_day(2022, 12, 29)

# For any given article, get the view count for a week or a month
client.get_article_views_for_week("Pelé", "20221218")
client.get_article_views_for_month("Lionel Messi", "20221201", "20221231")

# Retrieve the day of the month in which an article got the most page views 
client.get_most_article_views_in_month("Pelé", 2022, 12)
client.get_most_article_views_in_week("Kylian Mbappé", "20221218")
```

For complete documentation of all available client methods, see the [docs](https://github.com/sarahduve/wiki_api/tree/main/docs/wiki_api)!
```
$ open docs/wiki_api/index.html
```
## Notes

### Asynchronous API  Calls
I originally thought this would be a good opportunity to experiment with [asyncio](https://docs.python.org/3/library/asyncio.html) and [aiohttp](https://docs.aiohttp.org/en/stable/) given that `client.get_most_viewed_for_week()` makes seven separate calls to the API. But this would have required the user to be familiar with asynchronous programming and would necessitate the use of the async/await syntax for _every_ call, even ones that only requested one URL. I also wanted it to be as simple as possible to make calls from within the console. Though I did benchmark and the time savings were impressive, even when making a single call! In comparison, I also tried [requests-futures](https://pypi.org/project/requests-futures/) but saw no significant performance improvements, so I stayed with synchronous calls. 

I eventually saw meaningful gains by using threads via [ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor) (on average .35 seconds vs .5 seconds when the seven calls are made synchronously). Unfortunately at this point, I had already finalized my docs and test suite, so I decided that it wasn’t significant enough to merit the refactor. Obviously, I would do this in production, especially if I opened up additional methods that might make more than seven calls to the API.

### Other prod concerns

#### Dates!
If I were to use this in production, I think I would make it so methods could accept either date objects or `YYYYMMDD` formatted strings. If a dev were to use the wrapper programmatically, this would likely save them from converting back and forth to strings. As it is, I don’t love the inconsistency that some methods take `YYYYMMDD` strings and some take the year, month, and date separately as ints, but this is an inconsistency with the Wikipedia API itself, and I tried to relieve it by making int parameters come in the same order (year, month, day). 

Another compromise I made is by making weekly reporting on a rolling basis given a start date. I thought of using ISO week numbers in some way, but I would still need to account for differences in week starting days (i.e. Sunday vs. Monday). In production, I would also add more robust error handling, particularly when it comes to dates prior to July 2015. As it stands now, malformed articles, nonexistent articles, and requests for this time period before the pageviews API existed all return 404 errors. By handling pre-2015 dates on my side I could at least distinguish between “doesn’t exist” and “too old”. 

#### Caching and rate limiting
Wikipedia does its own rate limiting, but if I cached frequently requested GETs, I could make potentially make a lot fewer requests to the API and avoid being throttled.

#### Logging
I would add more!

### Weird Gotchas
Somewhat surprisingly, Wikipedia doesn’t have terribly consistent normalization where capitalization is concerned.
![image](https://user-images.githubusercontent.com/2575390/211652402-8a934152-59b2-4d93-98de-4a75056c56c9.png)
![image](https://user-images.githubusercontent.com/2575390/211652455-9324ef2a-4fa8-4788-b9e7-3956aca7f1fb.png)

That’s how it’s possible that these return two different values:
```
>>> client.get_article_views_for_month("Lionel messi", "20221201", "20221231")
16526
>>> client.get_article_views_for_month("Lionel Messi", "20221201", "20221231")
11561467
```

Because of that, I decided to leave capitalization as is when encoding user supplied article strings, however in prod I could potentially find a more robust way of dealing with this. 


## TODO
- [ ] Unit tests for WikiApiClient model
- [ ] Faster requests with aiohttp
- [ ] Allow methods to accept date strings or objects

