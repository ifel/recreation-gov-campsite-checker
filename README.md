# Campsite Availability Scraping

**This has been updated to work with the new recreation.gov site and API!!!**

This script scrapes the https://recreation.gov website for campsite availabilities.

## Example Usage
```
# Old way
$ python camping.py crawl --start-date 2018-07-20 --end-date 2018-07-23 232448 232450 232447 232770
❌ TUOLUMNE MEADOWS: 0 site(s) available out of 148 site(s)
🏕 LOWER PINES: 11 site(s) available out of 73 site(s)
❌ UPPER PINES: 0 site(s) available out of 235 site(s)
❌ BASIN MONTANA CAMPGROUND: 0 site(s) available out of 30 site(s)

# Using request
$ python recreation-gov-campsite-checker/camping.py crawl --exit_code --request "2019-10-11..2019-10-13:232448,232450,232447,232770;2019-11-18..2019-11-21:232448,232450,232447,232770"
There are campsites available from 2019-11-18 to 2019-11-21!!!
❌ TUOLUMNE MEADOWS (232448): 0 site(s) available out of 21 site(s)
❌ LOWER PINES (232450): 0 site(s) available out of 75 site(s)
🏕 UPPER PINES (232447): 142 site(s) available out of 240 site(s)
❌ BASIN MONTANA CAMPGROUND (232770): 0 site(s) available out of 30 site(s)

There are no campsites available from 2019-10-11 to 2019-10-13 :(
❌ TUOLUMNE MEADOWS (232448): 0 site(s) available out of 21 site(s)
❌ LOWER PINES (232450): 0 site(s) available out of 75 site(s)
❌ UPPER PINES (232447): 0 site(s) available out of 240 site(s)
❌ BASIN MONTANA CAMPGROUND (232770): 0 site(s) available out of 30 site(s)

# Get info of what we're looking for:
$ python recreation-gov-campsite-checker/camping.py crawl_info --request "2019-10-11..2019-10-13:232448,232450,232447,232770;2019-11-18..2019-11-21:232448,232450,232447,232770"
Looking for a place from 2019-11-18 to 2019-11-21 in:
- UPPER PINES
- TUOLUMNE MEADOWS
- LOWER PINES
- BASIN MONTANA CAMPGROUND

Looking for a place from 2019-10-11 to 2019-10-13 in:
- UPPER PINES
- TUOLUMNE MEADOWS
- BASIN MONTANA CAMPGROUND
- LOWER PINES

# Get info in the loop, and send info to telegram chat. Once it's started, it sends the info of the user requests to the chat, and then sends this info every $send_info_every (by default 24) hours. Once it finds anything, it sends the info to the chat, and will not try to find an availability for that user request within next $dont_recheck_avail_for seconds (15 minutes by default).

$ python recreation-gov-campsite-checker/camping.py crawl_loop --exit_code --only_available --html --request 2019-08-30..2019-09-02:233116,231959,233118,232491,272229,233359,232083,232874,232875,232876,232769,232768;2019-09-30..2019-10-02:233116,231959,233118,232491,272229,233359,232083,232874,232875,232876,232769,232768 --dont_recheck_avail_for 900 --telegram_token "abc" --telegram_chat_id "123"
[2019-09-15 20:59:08,924] INFO [Crawler._gen_telegram_config:64] Generating telegram config
[2019-09-15 20:59:08,925] INFO [Crawler.crawl_loop:28] Time to get search info
Looking for a place from 2019-08-30 to 2019-09-02 in:
- <a href="https://www.recreation.gov/camping/campgrounds/231959/">PLASKETT CREEK CAMPGROUND</a> (231959)
- <a href="https://www.recreation.gov/camping/campgrounds/232874/">WILLIAM KENT CAMPGROUND</a> (232874)
- <a href="https://www.recreation.gov/camping/campgrounds/233118/">PONDEROSA CAMPGROUND</a> (233118)
- <a href="https://www.recreation.gov/camping/campgrounds/232768/">Nevada Beach Campground and Day Use Pavilion</a> (232768)
- <a href="https://www.recreation.gov/camping/campgrounds/233359/">Point Reyes National Seashore Campground</a> (233359)
- <a href="https://www.recreation.gov/camping/campgrounds/232769/">FALLEN LEAF CAMPGROUND</a> (232769)
- <a href="https://www.recreation.gov/camping/campgrounds/232083/">SUNSET-UNION VALLEY</a> (232083)
- <a href="https://www.recreation.gov/camping/campgrounds/272229/">BICENTENNIAL CAMPGROUND</a> (272229)
- <a href="https://www.recreation.gov/camping/campgrounds/232876/">MEEKS BAY</a> (232876)
- <a href="https://www.recreation.gov/camping/campgrounds/233116/">KIRK CREEK CAMPGROUND</a> (233116)
- <a href="https://www.recreation.gov/camping/campgrounds/232491/">KIRBY COVE CAMPGROUND</a> (232491)
- <a href="https://www.recreation.gov/camping/campgrounds/232875/">KASPIAN CAMPGROUND</a> (232875)
Looking for a place from 2019-09-30 to 2019-10-02 in:
- <a href="https://www.recreation.gov/camping/campgrounds/232768/">Nevada Beach Campground and Day Use Pavilion</a> (232768)
- <a href="https://www.recreation.gov/camping/campgrounds/232769/">FALLEN LEAF CAMPGROUND</a> (232769)
- <a href="https://www.recreation.gov/camping/campgrounds/232083/">SUNSET-UNION VALLEY</a> (232083)
- <a href="https://www.recreation.gov/camping/campgrounds/233359/">Point Reyes National Seashore Campground</a> (233359)
- <a href="https://www.recreation.gov/camping/campgrounds/233116/">KIRK CREEK CAMPGROUND</a> (233116)
- <a href="https://www.recreation.gov/camping/campgrounds/232491/">KIRBY COVE CAMPGROUND</a> (232491)
- <a href="https://www.recreation.gov/camping/campgrounds/272229/">BICENTENNIAL CAMPGROUND</a> (272229)
- <a href="https://www.recreation.gov/camping/campgrounds/232876/">MEEKS BAY</a> (232876)
- <a href="https://www.recreation.gov/camping/campgrounds/232874/">WILLIAM KENT CAMPGROUND</a> (232874)
- <a href="https://www.recreation.gov/camping/campgrounds/232875/">KASPIAN CAMPGROUND</a> (232875)
- <a href="https://www.recreation.gov/camping/campgrounds/233118/">PONDEROSA CAMPGROUND</a> (233118)
- <a href="https://www.recreation.gov/camping/campgrounds/231959/">PLASKETT CREEK CAMPGROUND</a> (231959)

[2019-09-15 20:59:10,967] INFO [Crawler.crawl_loop:31] Getting availabilities
There are no campsites available from 2019-08-30 to 2019-09-02 :(

There are campsites available from 2019-09-30 to 2019-10-02!!!
- 🏕 <a href="https://www.recreation.gov/camping/campgrounds/231959/availability">PLASKETT CREEK CAMPGROUND</a> (231959): 3 site(s) available out of 46 site(s)
- 🏕 <a href="https://www.recreation.gov/camping/campgrounds/233359/availability">Point Reyes National Seashore Campground</a> (233359): 21 site(s) available out of 65 site(s)
- 🏕 <a href="https://www.recreation.gov/camping/campgrounds/232874/availability">WILLIAM KENT CAMPGROUND</a> (232874): 61 site(s) available out of 81 site(s)
- 🏕 <a href="https://www.recreation.gov/camping/campgrounds/232875/availability">KASPIAN CAMPGROUND</a> (232875): 8 site(s) available out of 9 site(s)
- 🏕 <a href="https://www.recreation.gov/camping/campgrounds/232876/availability">MEEKS BAY</a> (232876): 23 site(s) available out of 40 site(s)
- 🏕 <a href="https://www.recreation.gov/camping/campgrounds/232769/availability">FALLEN LEAF CAMPGROUND</a> (232769): 112 site(s) available out of 208 site(s)
- 🏕 <a href="https://www.recreation.gov/camping/campgrounds/232768/availability">Nevada Beach Campground and Day Use Pavilion</a> (232768): 4 site(s) available out of 56 site(s)

```

The script also accepts additional options:
- crawl command:
  - --html - print output with html formatting, useful for telegram
  - --only_available - print only available sites
  - --no_overall - if provided, prints out only camps info, no summary line
  - --exit_code - if something is found, exit code is 0, otherwise 61

- crawl_info command:
  - --html - print output with html formatting, useful for telegram

- crawl_loop command. It accepts all the crawl accepts plus:
  - --check_freq - Sleep time in secs between checks, default: 60
  - --dont_recheck_avail_for - Do not recheck available for this amount of secs, default: 900
  - --telegram_token - Send messages to telegram using this token
  - --telegram_chat_id - Send messages to telegram chat with this id
  - --send_info_every - Send info of active checks every (default: 24) hours

Send info to Telegram.
You must specify telegram_token and telegram_chat_id both.

You can also read from stdin. Define a file (e.g. `parks.txt`) with IDs like this:
```
232447
232449
232450
232448
```
and then use it like this:
```
$ python camping.py --start-date 2018-07-20 --end-date 2018-07-23 --stdin < parks.txt
```

You'll want to put this script into a 5 minute crontab. You could also grep the output for the success emoji (🏕) and then do something in response, like notify you that there is a campsite available. See the "Twitter Notification" section below.

## Getting park IDs
What you'll want to do is go to https://recreation.gov and search for the campground you want. Click on it in the search sidebar. This should take you to a page for that campground, the URL will look like `https://www.recreation.gov/camping/campgrounds/<number>`. That number is the park ID.

You can also take [this site for a spin](https://pastudan.github.io/national-parks/). Thanks to [pastudan](https://github.com/pastudan)!

## Installation

I wrote this in Python 3.7 but I've tested it as working with 3.5 and 3.6 also.
```
python3 -m venv myvenv
source myvenv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
# You're good to go!
```

## Development
This code is formatted using black and isort:
```
black -l 80 --py36 camping.py
isort camping.py
```
Note: `black` only really supports 3.6+ so watch out!

Feel free to submit pull requests, or look at the original: https://github.com/bri-bri/yosemite-camping

### Differences from the original
- Python 3 🐍🐍🐍.
- Park IDs not hardcoded, passed via the CLI instead.
- Doesn't give you URLs for campsites with availabilities.
- Works with any park out of the box, not just those in Yosemite like with the original.
- **Update 2018-10-21:** Works with the new recreation.gov site.

## Twitter Notification
If you want to be notified about campsite availabilities via Twitter (they're the only API out there that is actually easy to use), you can do this:
1. Make an app via Twitter. It's pretty easy, go to: https://apps.twitter.com/app/new.
2. Change the values in `twitter_credentials.py` to match your key values.
3. Pipe the output of your command into `notifier.py`. See below for an example.

```
python camping.py --start-date 2018-07-20 --end-date 2018-07-23 70926 70928 | python notifier.py @banool1
```

You'll want to make the app on another account (like a bot account), not your own, so you get notified when the tweet goes out.

I left my API keys in here but don't exploit them ty thanks.

**Thanks to https://github.com/bri-bri/yosemite-camping for getting me most of the way there for the old version.**
