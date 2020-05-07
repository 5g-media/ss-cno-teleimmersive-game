# SS-CNO for Tele-immersive game sessions - Training Dataset

This directory includes data that were collected and exploited in order to perform the initial training 
of the implemented Reinforcement Learning (RL) agent.

## Data Format

The data in this directory are saved in the form of experiences. Each line of each dataset file can be 
parsed as a JSON object, which has the following format:

```
[measurements_before_action, [action, action_value], measurents_after_action]
```

The `measurements_before_action` and `measurements_after_action` components of the above representation
are JSON objects including the complete vector of measurements before and after the execution of an 
action. The contents of each of the measurement JSON objects are the following fields:

  * bitrate_aggr (_float_): Aggregated Bit Rate as perceived by a spectator
  * bitrate_on (_float_): Bit rate as perceived by a spectator
  * framerate_aggr (_float_): Aggregated Frame Rate as perceived by a spectator
  * framerate_on (_float_): Frame Rate as perceived by a spectator
  * latency_aggr (_float_): Aggregated Latency as perceived by a spectator
  * mean_opinion_score (_float_): Mean Opinion Score (MOS) as perceived by a spectator
  * no_of_profiles_produced (_integer_): Number of transcoder-produced profiles
  * output_data_bytes (_integer_): Transcoder Output Data Bytes
  * percentage_of_gpu_users (_float_): Percentage of spectators that use a GPU
  * produced_profiles (_list_ of _integer_): The list of produced profiles
  * quality (_integer_): Quality consumed by a spectator
  * qoe_sum (_float_): Some of MOS for all spectators in the session
  * theoretic_load_percentage (_float_): Theoretic Load Percentage of a transcoder
  * transcoding_cost (_float_): Transcoding cost
  * working_fps (_float_): Working FPS of transcoder

The possible values for the `action` and `action_value` list are:

  * ["no_operation", null]
  * ["set_vtranscoder_client_profile", 0.0]
  * ["set_vtranscoder_client_profile", 1.0]
  * ["set_vtranscoder_client_profile", 2.0]
  * ["set_vtranscoder_client_profile", 3.0]
  * ["set_vtranscoder_client_profile", 4.0]
  * ["set_vtranscoder_client_profile", 5.0]

A sample line of the training file looks like this:

```json
[
   {
      "framerate_aggr": 16.56868261619503, 
      "latency_aggr": 0, 
      "percentage_of_gpu_users": 0.4, 
      "output_data_bytes": 154840, 
      "no_of_profiles_produced": 3, 
      "bitrate_on": 54.03364210583757, 
      "qoe_sum": 17.8261012801176, 
      "framerate_on": 18.36811519310523, 
      "bitrate_aggr": 147.07879835327776, 
      "quality": 5, 
      "mean_opinion_score": 3.515964987847363, 
      "transcoding_cost": 16.5, 
      "working_fps": 19.96406364440918, 
      "theoretic_load_percentage": 57.44755554199219, 
      "produced_profiles": [0, 1, 5]
   }, 
   ["set_vtranscoder_client_profile", 1.0], 
   {
      "framerate_aggr": 17.059889039547578, 
      "latency_aggr": 0, 
      "percentage_of_gpu_users": 0.0, 
      "output_data_bytes": 58562, 
      "no_of_profiles_produced": 3, 
      "bitrate_on": 180.8302834589164, 
      "qoe_sum": 19.1750493849463, 
      "framerate_on": 7.363285254834768, 
      "bitrate_aggr": 230.31595370729022, 
      "quality": 1, 
      "mean_opinion_score": 3.7687196558119145, 
      "transcoding_cost": 3.5, 
      "working_fps": 19.968050003051758, 
      "theoretic_load_percentage": 57.27770233154297, 
      "produced_profiles": [0, 1, 2]
   }
]
```

## Data Collection

The present dataset consists of measurements collected during 10 tele-immersive game sessions with pre-recorded
player streams. Random actions (of the aforementioned available ones) were executed upon the collection
of a set of measurements, while recording the initial set of measurements, the executed action and value,
and the set of measurements that was received after the action's execution.

For the collection of the dataset, three scenarios were formed:

  * The first scenario included spectators with high-bandwidth and processing power;
  * the second scenario included spectators on the other side of the spectrum, i.e. with low bandwidth and processing power;
  * and the spectators in the third scenario were a mixture of both.


## Selected Training Set

The selected training set is comprised of _4.381_ experiences, as previously described. The experiences
were randomly selected from the total of _20.000_ that were collected. Since RL was employed, there was no
need for a larger dataset (maybe even the 4.381 experiences were more than needed), as in case of many
experiences, the RL agent would find difficulties in adjusting accordingly to the needs of a deployment
with specific characteristics.
