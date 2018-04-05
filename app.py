import tensorflow as tf
import json
import numpy as np
from flask import Flask, request, jsonify,  render_template
from itertools import combinations, permutations
from heroes import Hero, RADIANT, DIRE

app = Flask(__name__, static_url_path='/static')

heroes_columns = tf.feature_column.numeric_column('heroes', (115,))
estimator = tf.estimator.DNNClassifier(
    feature_columns=[heroes_columns],
    hidden_units=[350, 225, 150, 100, 70, 45, 25, 10],
    model_dir='models/dnn_dota_dropout_serve'
)

# TODO: Maybe there should be Draft object in heroes.py?
def generate_inputs(team_vector, bans):
    dire_missing = 5 > np.sum(team_vector == DIRE)
    rad_missing = 5 > np.sum(team_vector == RADIANT)

    avail = available_pick_ids(team_vector, bans)

    inputs = [team_vector]
    if dire_missing:
        for h in avail:
            inputs.append(generate_vector(team_vector, [], [h]))

    if rad_missing:
        for h in avail:
            inputs.append(generate_vector(team_vector, [h], []))
    return np.array(inputs)

def predict(model, radiant, dire, bans):
    vec = Hero.vector_from_teams(radiant, dire)
    inputs = generate_inputs(vec, bans)
    predictions = model.predict(input_fn=tf.estimator.inputs.numpy_input_fn({'heroes': inputs}, shuffle=False))
    radiant_picks = {}
    dire_picks = {}
    probs = None
    for i, prediction in enumerate(predictions):
        new_pick_offsets = np.argwhere(inputs[i] - vec).flatten().tolist()
        dire_win, radiant_win = prediction['probabilities'].tolist()
        if not new_pick_offsets:
            dire
            probs = {'dire_win': dire_win, 'radiant_win': radiant_win}
        for o in new_pick_offsets:
            team = inputs[i][o]
            hero = Hero.by_offset(o)
            if team == RADIANT:
                radiant_picks[hero.id] = {
                    'id': hero.id,
                    'name': hero.name,
                    'win': radiant_win,
                    'advantages': hero.advantages(dire),
                    'synergies': hero.synergies(radiant)
                }
            else: # team == DIRE
                dire_picks[hero.id] = {
                    'id': hero.id,
                    'name': hero.name,
                    'win': dire_win,
                    'advantages': hero.advantages(radiant),
                    'synergies': hero.synergies(dire)
                }

    return {
        'picks': {
            'radiant': sorted(radiant_picks.values(), key=lambda x: -x['win']),
            'dire': sorted(dire_picks.values(), key=lambda x: -x['win'])
        },
        'probs': probs
    }

def available_pick_ids(team_vector, bans):
    available_ids = Hero.all_ids()
    available_ids -= set(bans)
    picked_offsets = np.argwhere(team_vector).flatten().tolist()
    picked_ids = {Hero.by_offset(x).id for x in picked_offsets}
    return available_ids - picked_ids

def generate_vector(v, r, d):
    v = np.copy(v)
    for rad in r:
        v[Hero.by_id(rad).offset] = RADIANT
    for dire in d:
        v[Hero.by_id(dire).offset] = DIRE
    return v

def parse(radiant, dire, bans):
    def x(a):
        if a == '-':
            return []
        return [Hero.by_id(int(s)) for s in a.split(',')]
    return x(radiant), x(dire), x(bans)

@app.route('/')
def root():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/match/<string:radiant>/<string:dire>/<string:bans>/')
def match(radiant, dire, bans):
    radiant, dire, bans = parse(radiant, dire, bans)
    app.logger.info("teams are radiant: {}, dire: {}, bans: {}".format(radiant, dire, bans))
    if len(radiant) > 5 or len(dire) > 5:
        res = {"msg" : "Only five members per team please"}
    else:
        res = predict(estimator, radiant, dire, bans)

    return jsonify(res)
