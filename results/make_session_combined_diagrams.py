import os

combined_data = '{}/{}/combined/session/data/{}.dat'

for scenario_dir in next(os.walk('.'))[1]:
    for run in next(os.walk(scenario_dir))[1]:
        average_mos = combined_data.format(scenario_dir, run, 'average_mos')
        no_of_produced_profiles = combined_data.format(scenario_dir, run, 'number_of_produced_profiles')
        percentage_of_gpu_users = combined_data.format(scenario_dir, run, 'percentage_of_gpu_users')
        transcoding_cost = combined_data.format(scenario_dir, run, 'transcoding_cost')
        os.system('gnuplot -e '
                  '"set term png size 1000,1000; '
                  'set size 1, 1; '
                  'set origin 0, 0; '
                  'set output \'{}/{}/combined/session/session_diagram.png\'; '
                  'set multiplot layout 4, 1 scale 0.8, 0.9; '
                  'set notitle; '
                  'set tmargin 2; '
                  'set title \'Average Mean Opinion Score (MOS)\'; '
                  'set yrange [0:5]; '
                  'set xrange [0:]; '
                  'plot \'{}\' using 1:2 with line title \'player_1\', \'{}\' using 1:3 with line title \'player_2\'; '
                  'set title \'Number of Produced Profiles\'; '
                  'set yrange [0:5]; '
                  'set xrange [0:]; '
                  'plot \'{}\' using 1:2 with line title \'player_1\', \'{}\' using 1:3 with line title \'player_2\'; '
                  'set title \'Percentage of GPU Users\'; '
                  'set yrange [0:100]; '
                  'set xrange [0:]; '
                  'plot \'{}\' using 1:2 with line title \'player_1\', \'{}\' using 1:3 with line title \'player_2\'; '
                  'set title \'Transcoding Cost\'; '
                  'set yrange [0:20]; '
                  'set xrange [0:]; '
                  'plot \'{}\' using 1:2 with line title \'player_1\', \'{}\' using 1:3 with line title \'player_2\'; '
                  'unset multiplot; '
                  'unset output"'
                  .format(scenario_dir, run, average_mos, average_mos, no_of_produced_profiles, no_of_produced_profiles,
                          percentage_of_gpu_users, percentage_of_gpu_users, transcoding_cost, transcoding_cost))
