import json
import numpy as np
import pickle

RADIANT=1
DIRE=-1

SYNERGIES = pickle.load(open('data/synergy.p','rb'))
def synergy(a,b):
    syn = SYNERGIES[(a,b)] if b > a else SYNERGIES[(b,a)]
    syn['name'] = Hero.by_id(b).name

    if syn['synergy'] > 0:
        verb = 'performs'
    else:
        verb = "doesn't perform"
    syn['desc'] = "{} {} well with {} with synergy of {:.2%}. They have win rate of {:.2%} together over {} matches".format(
        Hero.by_id(a).name,
        verb,
        Hero.by_id(b).name,
        syn['synergy'],
        syn['win_chance'],
        syn['n'])

    syn['value'] = syn['synergy']
    syn['otherId'] = b
    return syn

ADVANTAGES = pickle.load(open('data/advantage.p','rb'))
def advantage(a,b):
    adv = ADVANTAGES[(a,b)]
    opponent = Hero.by_id(b)
    adv['name'] = opponent.name
    if adv['advantage'] > 0:
        verb = 'performs'
    else:
        verb = "doesn't perform"

    adv['desc'] = "{} {} well against {} with advantage of {:.2%} with win rate of {:.2%} over {} matches".format(
        Hero.by_id(a).name,
        verb,
        opponent.name,
        adv['advantage'],
        adv['win_chance'],
        adv['n'])

    adv['value'] = adv['advantage']
    return adv

class Hero:
    __heroes_by_offset = {}
    __heroes_by_id = {}

    def __init__(self, offset, id, name):
        self.id = id
        self.offset = offset
        self.name = name
        Hero.__heroes_by_offset[offset] = self
        Hero.__heroes_by_id[id] = self

    @staticmethod
    def by_offset(offset):
        return Hero.__heroes_by_offset[offset]

    @staticmethod
    def by_id(id):
        return Hero.__heroes_by_id[id]

    def all_ids():
        return Hero.__heroes_by_id.keys()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

    def synergies(self, with_):
        return [synergy(self.id, hero.id) for hero in with_]

    def advantages(self, over):
        return [advantage(self.id, hero.id) for hero in over]

    @staticmethod
    def vector_from_teams(radiant, dire):
        v = np.zeros(len(Hero.__heroes_by_offset), np.int8)
        for player in radiant:
            v[player.offset] = RADIANT

        for player in dire:
            v[player.offset] = DIRE

        return np.array(v)

def load_heroes():
    data = json.load(open('./static/heroes.json'))

    for offset, x in enumerate(data):
        Hero(offset, x['id'], x['localized_name'])

load_heroes()
