set style fill solid 0.25 border -1
set style boxplot nooutliers #pointtype 7
set style data boxplot
set title 'Average MOS' font 'Arial, 14';
set xtics ('00, 1, 00, 00, 00, Player 1' 1, '00, 1, 00, 00, 00, Player 2' 2, '02, 02, 02, 02, 02, Player 1' 3, '02, 02, 02, 02, 02, Player 2' 4, '02, 04, 015, 01, 015, Player 1' 5, '02, 04, 015, 01, 015, Player 2' 6, '02, 06, 00, 00, 02, Player 1' 7, '02, 06, 00, 00, 02, Player 2' 8, '035, 01, 01, 01, 035, Player 1' 9, '035, 01, 01, 01, 035, Player 2' 10, '03, 03, 00, 01, 03, Player 1' 11, '03, 03, 00, 01, 03, Player 2' 12)
plot for [i=1:12] 'all_scenarios_combined_data/average_mos.dat' using (i):i notitle