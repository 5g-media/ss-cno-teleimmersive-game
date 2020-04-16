# SS-CNO for Tele-immersive game sessions

This component is part of the 5G-MEDIA MAPE service. Take a look in the [MAPE](https://github.com/5g-media/mape) repository.

## Introduction

This is the repository for the servce-specific Cognitive Network Optimizer (SS-CNO) for UC1 of the 5G-Media project. The purpose of the 
CNO is to decide the actions that should be taken regarding a Network Service (NS) or Virtual Network Function 
(VNF) based on the monitoring metrics that are received from the (A)nalysis part of the MAPE loop.

## Algorithm

The CNO implements two Reinforcement Learning (RL) models based on [Markov Decision Processes](https://en.wikipedia.org/wiki/Markov_decision_process) (MDP) with [Prioritized Sweeping](http://www.incompleteideas.net/book/ebook/node98.html). In the first model (MDP) the state space
is stable throughout the execution of the algorithm, while in the second model an adaptive state space partitioning is carried out, exploiting a Decision Tree based approach, leading to a fine-grained
splitting of the state space.

The implementation of these algorithms is inspired from a [paper](https://arxiv.org/abs/1702.02978) entitled ___Elastic Resource Management with Adaptive State Space Partitioning of Markov Decision Processes___.
The code related to this paper can be found on [github](https://github.com/klolos/reinforcement_learning). This code was used as a basis but became functional after
a major refactoring. For details on the overall concept of the algorithm please refer to the aforementioned publication.

### Reward Functions

The reward function is considered the most important component of a RL algorithm as it is capable of assisting the fast
convergence of the algorithm. Additionally, if multiple reward functions are implemented, optimizations aiming at different
aspects of the system can be applied. In our implementation five reward components have been implemented, targeting at:

  * **GPU usage**, positive if the application is deployed on a CPU-only node, due to the substantially low cost of such a node, or a GPU-node is used by the majority of spectators, and negative otherwise;
  * **QoE of single spectator**, defined as the percentage of increment or decrement of QoE of a spectator after the execution of a certain action;
  * **Combination of QoE & transcoding cost**, positive in case the QoE sum of all spectators is greater than the transcoding cost, or negative otherwise;
  * **Monitoring parameters**, depending on the percentage of increment or decrement of selected parameters, namely, a spectator’s bit rate and frame rate, following the execution of a certain action;
  * **Number  of  produced  profiles**, which gives a positive reward if the number of produced profiles is reduced and a negative reward if it is increased. 

The user can set different weights on these reward components depending on the focus of the optimization. The sum of all
weights should be equal to 1 (one).

## Installation Guide

### Prerequisites

For the deployment of the Cognitive Network Optimizer the Docker engine as well as docker-compose should be installed.
These actions can be performed following the instructions provided below. Firstly, an update should be performed
and essential packages should be installed:

```bash
sudo apt-get update
sudo apt-get install -y \
     apt-transport-https \
     ca-certificates \
     curl \
     software-properties-common
```

Secondly the key and Docker repository should be added:

```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository \
     "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
     $(lsb_release -cs) \
     stable"
```

Then another update is performed, Docker is installed and the user is added to docker group.

```bash
sudo apt-get update
sudo apt-get install -y docker-ce
sudo groupadd docker
sudo usermod -aG docker $USER
```

Finally, docker-compose should be installed:

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/1.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Environmental Parameters

**Docker Containers**

| Parameter | Description |
| --------- | ----------- |
| COMPOSE_PROJECT_NAME | The name of the project |
| PG_IMAGE_TAG | Postgres Docker image tag |
| PG_PORT | Postgres Port |
| PG_USER | Postgres User |
| PG_PASSWORD | Postgres Password |
| PG_DB | Postgres DB Name |
| RMQ_IMAGE_TAG | RabbitMQ Docker image tag |
| RMQ_USERNAME | RabbitMQ Username |
| RMQ_PASSWORD | RabbitMQ Password |

**Internal Settings**

| Parameter | Description |
| --------- | ----------- |
| CNO_IM_DEBUG | Debug enabled |
| CNO_IM_SUPERVISOR_PORT | Supervisor Port |
| CNO_IM_DB_HOST | DB Host |
| CNO_IM_DB_PORT | DB Port |
| CNO_IM_DB_USER | DB User |
| CNO_IM_DB_PASSWORD | DB Password |
| CNO_IM_DB_NAME | DB Name |
| CNO_IM_RMQ_USER | RabbitMQ Username |
| CNO_IM_RMQ_PASSWORD | RabbitMQ Password |
| CNO_IM_RMQ_HOST | RabbitMQ Host |
| CNO_IM_KAFKA_SERVER | Kafka Host URL |
| CNO_IM_COST | Weight of Cost-based reward (default: 0.2)|
| CNO_IM_QOE | Weight of QoE-based reward (default: 0.3) |
| CNO_IM_QOE_COST_COMBINED | Weight of QoE-and-Cost Combined reward (default: 0.2) |
| CNO_IM_MEASUREMENTS | Weight of Measurement-based reward (default: 0.1)|
| CNO_IM_NO_OF_PROFILES | Weight of Number of Profiles-based reward (default: 0.2) |s
| CNO_IM_TRAINING_FILE | Path of training file |
| CNO_IM_RESULTS_FILE | Path of results file |

### Deployment

The CNO is deployed as a collection of Docker containers, utilizing docker-compose. Having cloned the
code of this repository, and having created the .env file in *cognitive-network-optimizer* directory the following 
commands should be executed:

```bash
# download code
cd cognitive-network-optimizer
docker-compose up -d --build
```

### Included Applications

The applications running in this version of the CNO are the following, and can be monitored through the Supervisor web UI,
listening on the port set through the **CNO_IM_SUPERVISOR_PORT** as stated previously.

  * **Cognitive Network Optimizer**: The main application.
  * **Experience Collector**: An application targeting to the collection of experiences. It executes randomly selected actions and records the metrics before and after the execution, as well as the executed action. It can be used for the construction of a dataset.
  * **Spectator Recorder and Initializer**: It records the running spectators and sends the essential initialization message.
  * **Lifecycle Management**: Since FaaS services are allowed to run for an hour, this application cleans the old spectators and transcoders.
  * **Metric Collector**: This is the application which collects the measurements required by the CNO and combines them in a vector.
  
Except for the Experience Collector which should be started explicitly through the Supervisor web UI all
of the above applications are executed by default.

## Authors
- Singular Logic

## Contributors
 - Contact with Authors
 
## Acknowledgements
This project has received funding from the European Union’s Horizon 2020 research and innovation programme under grant agreement No 761699. The dissemination of results herein reflects only the author’s view and the European Commission is not responsible for any use that may be made of the information it contains.

## License
[Apache 2.0](LICENSE.md)