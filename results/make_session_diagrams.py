import os

labels = [('Number of Produced Profiles', 'number_of_produced_profiles'),
          ('Percentage of GPU Users', 'percentage_of_gpu_users'),
          ('Average Mean Opinion Score (MOS)', 'average_mos'),
          ('Transcoding Cost', 'transcoding_cost'),
          ('QoE Sum to Cost Rate', 'qoe_sum_to_cost_rate')]
session_data = '{}/{}/{}/session/data/{}.dat'

for scenario_dir in next(os.walk('.'))[1]:
    for run in next(os.walk(scenario_dir))[1]:
        for transcoder in ['transcoder_1', 'transcoder_2']:
            average_mos = session_data.format(scenario_dir, run, transcoder, 'average_mos')
            no_of_produced_profiles = session_data.format(scenario_dir, run, transcoder, 'number_of_produced_profiles')
            percentage_of_gpu_users = session_data.format(scenario_dir, run, transcoder, 'percentage_of_gpu_users')
            transcoding_cost = session_data.format(scenario_dir, run, transcoder, 'transcoding_cost')
            os.system('gnuplot -e '
                      '"set term png size 1000,1000; '
                      'set size 1, 1; '
                      'set origin 0, 0; '
                      'set output \'{}/{}/{}/session_diagram.png\'; '
                      'set multiplot layout 4, 1 scale 0.8, 0.9; '
                      'set notitle; '
                      'set tmargin 2; '
                      'set title \'Average Mean Opinion Score (MOS)\'; '
                      'set yrange [0:5]; '
                      'set xrange [0:]; '
                      'unset key; '
                      'plot \'{}\' using 1:2 with line; '
                      'set title \'Number of Produced Profiles\'; '
                      'set yrange [0:5]; '
                      'set xrange [0:]; '
                      'unset key; '
                      'plot \'{}\' using 1:2 with line; '
                      'set title \'Percentage of GPU Users\'; '
                      'set yrange [0:100]; '
                      'set xrange [0:]; '
                      'unset key; plot \'{}\' using 1:2 with line; '
                      'set title \'Transcoding Cost\'; '
                      'set yrange [0:20]; '
                      'set xrange [0:]; '
                      'unset key; '
                      'plot \'{}\' using 1:2 with line; '
                      'unset multiplot; '
                      'unset output"'
                      .format(scenario_dir, run, transcoder, average_mos, no_of_produced_profiles,
                              percentage_of_gpu_users, transcoding_cost))
