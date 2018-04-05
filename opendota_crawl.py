import requests
from time import time, sleep
import os
import gzip
import json
from glob import glob
from random import shuffle

# Lower start time limit for matches we're interested in
GENESIS = 1513728000 # https://dota2.gamepedia.com/Version_7.07d

# requests to opendota api throttled to occur at most every THROTTLE seconds
THROTTLE = 0.3
def throttle():
    while throttle.t and throttle.t + THROTTLE > time():
        sleep(0.1)
    throttle.t = time()
throttle.t = 0

# seed accound_ids from https://api.opendota.com/api/live
def seed_account_ids():
    throttle()
    r = requests.get('https://api.opendota.com/api/live')
    ids = []
    for match in r.json():
        for player in match['players']:
            ids.append(player['account_id'])
    return ids

# from those accounts_ids get match listing https://api.opendota.com/api/players/400502427/matches
def fetch_account(account_id):
    throttle()
    r = requests.get('https://api.opendota.com/api/players/{}/matches'.format(account_id))
    matches = r.json()
    #print(matches)
    matches = filter(lambda x: x['start_time'] > GENESIS, matches)
    matches = filter(lambda x: x['lobby_type'] == 7, matches)   # Only competitive games
    return map(lambda x: x['match_id'], matches)

# fetch individual matches from https://api.opendota.com/api/matches/3256289407
def fetch_match(match_id):
    throttle()
    r = requests.get('https://api.opendota.com/api/matches/{}'.format(match_id))
    match = r.json()
    ids = []
    for player in match['players']:
        if player['account_id']:
            ids.append(player['account_id'])
    return ids, r.text

# main loop
accounts_to_crawl = []
accounts_crawled = set()
matches_to_crawl = []
matches_crawled = set()
match_strings = []

for file in glob("crawled_matches/*.txt.gz"): # fix this
    print("processing {}".format(file))
    with gzip.open(file, 'rb') as f:
        file_content = f.read().decode("utf-8")
        for line in file_content.split("\n"):
            match = json.loads(line)
            matches_crawled.add(match['match_id'])
            for player in match['players']:
                if player['account_id']: accounts_to_crawl.append(player['account_id'])

print("starting accounts_to_crawl size: {} matches_crawled: {}".format(len(accounts_to_crawl), len(matches_crawled)))

while True:
    print("accounts_to_crawl={} accounts_crawled={} matches_to_crawl={} matches_crawled={}".format(
        len(accounts_to_crawl), len(accounts_crawled), len(matches_to_crawl), len(matches_crawled)
    ))

    while not accounts_to_crawl and not matches_to_crawl:
        print("seeding")
        accounts_to_crawl += seed_account_ids()

    shuffle(matches_to_crawl)
    
    while matches_to_crawl:
        match_id = matches_to_crawl.pop()
        if match_id not in matches_crawled:
            print("fetching match {}".format(match_id))
            try:
                account_ids, match_text = fetch_match(match_id)
                match_strings.append(match_text)
                for account_id in account_ids:
                    if account_id not in accounts_crawled and account_id not in matches_to_crawl:
                        accounts_to_crawl.append(account_id)
                matches_crawled.add(match_id)
                if len(matches_to_crawl) < 500:
                    break
            except Exception as e:
                print("fetch_match error", e)
                sleep(1)
                
    shuffle(accounts_to_crawl)
    
    while accounts_to_crawl and len(matches_to_crawl) < 1000:
        account_id = accounts_to_crawl.pop()
        if account_id not in accounts_crawled:
            print("fetching account {}".format(account_id))

            try:
                match_ids = fetch_account(account_id)
                for i in match_ids:
                    if i not in matches_crawled and i not in matches_to_crawl:
                        matches_to_crawl.append(i)
                accounts_crawled.add(account_id)
            except Exception as e:
                print("fetch_account error", e)
                sleep(1)

    if len(match_strings) >= 100:
        # save them
        directory = 'crawled_matches'
        if not os.path.exists(directory):
            os.makedirs(directory)

        output_file = os.path.join(directory, "{}.txt.gz".format(int(time())))
        with gzip.open(output_file, 'wb') as f:
            f.write(u"\n".join(match_strings).encode('utf-8'))
        print("wrote matches")
        match_strings = []
