import os
import json

import PyGnuplot as gp

labels = [('Mean Opinion Score', 'mean_opinion_score'),
          ('Frame Rate', 'frame_rate'),
          ('Consumed Profile', 'profile')]
spectator_data = '{}/{}/transcoder_{}/spectators/{}/data/{}.txt'

for scenario_dir in next(os.walk('.'))[1]:
    for run in next(os.walk(scenario_dir))[1]:
        with open('{}/{}/{}.txt'.format(scenario_dir, run, run)) as collected_measurements:
            spectators_and_trans = dict()
            for line in collected_measurements:
                previous_measurements, action, after_measurements = json.loads(line)
                client_id = previous_measurements.pop('client_id')
                transcoder_no = previous_measurements.pop('transcoder_no')
                if (client_id, transcoder_no) in spectators_and_trans.keys():
                    spectators_and_trans[(client_id, transcoder_no)]['mean_opinion_score'].extend(
                        [previous_measurements['mean_opinion_score'], after_measurements['mean_opinion_score']])
                    spectators_and_trans[(client_id, transcoder_no)]['frame_rate'].extend(
                        [previous_measurements['framerate_on'], after_measurements['framerate_on']])
                    spectators_and_trans[(client_id, transcoder_no)]['profile'].extend(
                        [previous_measurements['quality'], after_measurements['quality']])
                else:
                    spectators_and_trans.update({
                        (client_id, transcoder_no): {
                            'mean_opinion_score': [previous_measurements['mean_opinion_score'],
                                                   after_measurements['mean_opinion_score']],
                            'frame_rate': [previous_measurements['framerate_on'],
                                           after_measurements['framerate_on']],
                            'profile': [previous_measurements['quality'],
                                        after_measurements['quality']]
                        }
                    })
        for key in spectators_and_trans.keys():
            for metric in spectators_and_trans[key].keys():
                filename = spectator_data.format(scenario_dir, run, key[1], key[0], metric)
                if not os.path.exists(os.path.dirname(filename)):
                    os.makedirs(os.path.dirname(filename))
                X = spectators_and_trans[key][metric]
                Y = list(range(0, len(spectators_and_trans[key][metric])))
                gp.s([Y, X], filename)
