set size 1, 1
set origin 0, 0
set output '01_01_06_01_01_run_01_trans_01.png'
set multiplot layout 4, 1 scale 0.8, 0.9
set notitle
set tmargin 2

set title "Average Mean Opinion Score (MOS)"
set yrange [0:5]
set xrange [0:]
unset key
plot 'data/average_mos.dat' using 1:2 with line

set title "Number of Produced Profiles"
set yrange [0:5]
set xrange [0:]
unset key
plot 'data/number_of_produced_profiles.dat' using 1:2 with line

set title "Percentage of GPU Users"
set yrange [0:1.2]
set xrange [0:]
unset key
plot 'data/percentage_of_gpu_users.dat' using 1:2 with line

set title "Transcoding Cost"
set yrange [0:16]
set xrange [0:]
unset key
plot 'data/transcoding_cost.dat' using 1:2 with line

unset multiplot
unset output