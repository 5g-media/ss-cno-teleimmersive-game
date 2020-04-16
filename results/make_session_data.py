import os
import json

import PyGnuplot as gp

labels = [('Number of Produced Profiles', 'number_of_produced_profiles'),
          ('Percentage of GPU Users', 'percentage_of_gpu_users'),
          ('Average Mean Opinion Score (MOS)', 'average_mos'),
          ('Transcoding Cost', 'transcoding_cost'),
          ('QoE Sum to Cost Rate', 'qoe_sum_to_cost_rate')]
session_data = '{}/{}/{}/session/data/{}.dat'
combined_data = '{}/{}/combined/session/data/{}.dat'
stacked_run_data = '{}/{}.dat'
all_stacked_data = 'all_scenarios_combined_data/{}.dat'

for scenario_dir in sorted(next(os.walk('.'))[1]):
    for run in next(os.walk(scenario_dir))[1]:
        no_of_profiles_produced = {'transcoder_1': [], 'transcoder_2': []}
        percentage_of_gpu_users = {'transcoder_1': [], 'transcoder_2': []}
        mean_mos = {'transcoder_1': [], 'transcoder_2': []}
        transcoding_cost = {'transcoder_1': [], 'transcoder_2': []}
        qoe_sum_to_cost_rate = {'transcoder_1': [], 'transcoder_2': []}
        qoe_sum = {'transcoder_1': [], 'transcoder_2': []}
        with open('{}/{}/{}.txt'.format(scenario_dir, run, run)) as collected_measurements:
            for line in collected_measurements:
                previous_measurements, action, after_measurements = json.loads(line)
                no_of_profiles_produced['transcoder_{}'.format(previous_measurements['transcoder_no'])].append(
                    previous_measurements['no_of_profiles_produced'] - 1)
                no_of_profiles_produced['transcoder_{}'.format(previous_measurements['transcoder_no'])].append(
                    after_measurements['no_of_profiles_produced'] - 1)
                percentage_of_gpu_users['transcoder_{}'.format(previous_measurements['transcoder_no'])].append(
                    previous_measurements['percentage_of_gpu_users'] * 100)
                percentage_of_gpu_users['transcoder_{}'.format(previous_measurements['transcoder_no'])].append(
                    after_measurements['percentage_of_gpu_users'] * 100)
                mean_mos['transcoder_{}'.format(previous_measurements['transcoder_no'])].append(
                    previous_measurements['qoe_sum'] / 5)
                mean_mos['transcoder_{}'.format(previous_measurements['transcoder_no'])].append(
                    after_measurements['qoe_sum'] / 5)
                transcoding_cost['transcoder_{}'.format(previous_measurements['transcoder_no'])].append(
                    previous_measurements['transcoding_cost'])
                transcoding_cost['transcoder_{}'.format(previous_measurements['transcoder_no'])].append(
                    after_measurements['transcoding_cost'])
                qoe_sum_to_cost_rate['transcoder_{}'.format(previous_measurements['transcoder_no'])].append(
                    previous_measurements['qoe_sum'] / previous_measurements['transcoding_cost'])
                qoe_sum_to_cost_rate['transcoder_{}'.format(previous_measurements['transcoder_no'])].append(
                    after_measurements['qoe_sum'] / after_measurements['transcoding_cost'])
                qoe_sum['transcoder_{}'.format(previous_measurements['transcoder_no'])].append(
                    previous_measurements['qoe_sum'])
                qoe_sum['transcoder_{}'.format(previous_measurements['transcoder_no'])].append(
                    after_measurements['qoe_sum'])
            metrics = [(labels[0], no_of_profiles_produced), (labels[1], percentage_of_gpu_users),
                       (labels[2], mean_mos), (labels[3], transcoding_cost), (labels[4], qoe_sum_to_cost_rate)]
            for label, metric in metrics:
                diagram_label, file_label = label
                for key in metric.keys():
                    filename = session_data.format(scenario_dir, run, key, file_label)
                    if not os.path.exists(os.path.dirname(filename)):
                        os.makedirs(os.path.dirname(filename))
                    X = metric[key]
                    Y = list(range(0, len(metric[key])))
                    gp.s([Y, X], filename)
                filename = combined_data.format(scenario_dir, run, file_label)
                if not os.path.exists(os.path.dirname(filename)):
                    os.makedirs(os.path.dirname(filename))
                X = metric['transcoder_1']
                Z = metric['transcoder_2']
                # len_x, len_z = len(X), len(Z)
                # X = X[:len_z] if len_x > len_z else X
                # Z = Z[:len_x] if len_z > len_x else Z
                # Y = list(range(0, len(X)))
                # gp.s([Y, X, Z], filename)
                # stacked_data_filename = stacked_run_data.format(scenario_dir, file_label)
                # all_stacked_data_filename = all_stacked_data.format(file_label)
                # if not os.path.exists(os.path.dirname(stacked_data_filename)):
                #     os.makedirs(os.path.dirname(stacked_data_filename))
                # print('{}/{}'.format(scenario_dir, run))
                # os.system("cut -d' ' -f2-2 {} >> {}".format(filename, stacked_data_filename))
                # os.system("cut -d' ' -f3-3 {} >> {}".format(filename, stacked_data_filename))
                X.extend(Z)
                Y = list(range(0, len(X)))
                gp.s([Y, X], filename)
                stacked_data_filename = stacked_run_data.format(scenario_dir, file_label)
                all_stacked_data_filename = all_stacked_data.format(file_label)
                if not os.path.exists(os.path.dirname(stacked_data_filename)):
                    os.makedirs(os.path.dirname(stacked_data_filename))
                print('{}/{}'.format(scenario_dir, run))
                os.system("cut -d' ' -f2-2 {} >> {}".format(filename, stacked_data_filename))
