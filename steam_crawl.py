import requests
from time import time, sleep
import os
import gzip
import json
from glob import glob
from random import shuffle, randint
from settings import STEAM_KEY

START_SEQ_NUM = 3155571979
THROTTLE = 1.0
directory = 'crawled_matches_steam'

def throttle():
    while throttle.t and throttle.t + THROTTLE > time():
        sleep(0.1)
    throttle.t = time()
throttle.t = 0

def get_matches(seq_num):
    throttle()
    payload = {'key': STEAM_KEY, 'start_at_match_seq_num': seq_num}
    r = requests.get('http://api.steampowered.com/IDOTA2Match_570/GetMatchHistoryBySequenceNum/v1', params=payload)
    matches = r.json()['result']['matches']
    last_seq_num = matches[-1]['match_seq_num']
    get_matches.latest_ts = max(get_matches.latest_ts, matches[-1]['start_time'])
    if randint(0, 10) == 0:
        print("{} days behind".format((time() - get_matches.latest_ts) / (3600*24)))
    return last_seq_num, list(filter(lambda x: x['lobby_type'] == 7, matches))
get_matches.latest_ts = 0

def save_matches(matches):
    if not os.path.exists(directory):
        os.makedirs(directory)

    seq_num = matches[1]['match_seq_num']
    output_file = os.path.join(directory, "{}.txt.gz".format(seq_num))
    with gzip.open(output_file, 'wb') as f:
        for match in matches:
            json_string = json.dumps(match, separators=(',', ':'))
            f.write((json_string + "\n").encode('utf-8'))
    print("wrote matches.")

def get_start_seq_num():
    seq_num = START_SEQ_NUM
    with gzip.open(glob("{}/*.txt.gz".format(directory))[-1], 'rb') as f:
        file_content = f.read().decode("utf-8")
        for line in file_content.split("\n"):
            try:
                match = json.loads(line)
                seq_num = max(seq_num, match['match_seq_num'])
            except Exception as e:
                pass # ignore the final empty line
    return seq_num

next_seq = get_start_seq_num()
crawled_matches = []
while True:
    try:
        next_seq, matches = get_matches(next_seq)
        crawled_matches += matches
        if len(crawled_matches) > 10000:
            save_matches(crawled_matches)
            crawled_matches = []
    except Exception as e:
        print(e)
        sleep(30)
