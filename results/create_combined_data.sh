#!/usr/bin/env bash


paste -d' ' 00_1_00_00_00/average_mos.dat \
           02_02_02_02_02/average_mos.dat \
           02_04_015_01_015/average_mos.dat \
           02_06_00_00_02/average_mos.dat \
           03_03_00_01_03/average_mos.dat \
           035_01_01_01_035/average_mos.dat \
           > all_scenarios_combined_data/average_mos.dat
paste -d' ' 00_1_00_00_00/number_of_produced_profiles.dat \
           02_02_02_02_02/number_of_produced_profiles.dat \
           02_04_015_01_015/number_of_produced_profiles.dat \
           02_06_00_00_02/number_of_produced_profiles.dat \
           03_03_00_01_03/number_of_produced_profiles.dat \
           035_01_01_01_035/number_of_produced_profiles.dat \
           > all_scenarios_combined_data/number_of_produced_profiles.dat
paste -d' ' 00_1_00_00_00/percentage_of_gpu_users.dat \
           02_02_02_02_02/percentage_of_gpu_users.dat \
           02_04_015_01_015/percentage_of_gpu_users.dat \
           02_06_00_00_02/percentage_of_gpu_users.dat \
           03_03_00_01_03/percentage_of_gpu_users.dat \
           035_01_01_01_035/percentage_of_gpu_users.dat \
           > all_scenarios_combined_data/percentage_of_gpu_users.dat
paste -d' ' 00_1_00_00_00/qoe_sum_to_cost_rate.dat \
           02_02_02_02_02/qoe_sum_to_cost_rate.dat \
           02_04_015_01_015/qoe_sum_to_cost_rate.dat \
           02_06_00_00_02/qoe_sum_to_cost_rate.dat \
           03_03_00_01_03/qoe_sum_to_cost_rate.dat \
           035_01_01_01_035/qoe_sum_to_cost_rate.dat \
           > all_scenarios_combined_data/qoe_sum_to_cost_rate.dat
paste -d' ' 00_1_00_00_00/transcoding_cost.dat \
           02_02_02_02_02/transcoding_cost.dat \
           02_04_015_01_015/transcoding_cost.dat \
           02_06_00_00_02/transcoding_cost.dat \
           03_03_00_01_03/transcoding_cost.dat \
           035_01_01_01_035/transcoding_cost.dat \
           > all_scenarios_combined_data/transcoding_cost.dat