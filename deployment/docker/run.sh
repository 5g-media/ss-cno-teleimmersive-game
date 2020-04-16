#!/usr/bin/env bash

# Work dir
cd /opt/cognitive-network-optimizer

# In case of simulation the simulated metric publisher is needed
if [[ "${1}" == "simulation" ]]
then
    cd /opt/cognitive-network-optimizer
    rm /etc/supervisor/conf.d/cognitive-network-optimizer.conf
    cp deployment/supervisor/simulation.conf /etc/supervisor/conf.d/simulation.conf
fi

# Wait for Postgres and make migrations
while ! nc -z cno_im_postgres 5432; do
  echo "Waiting for PostgreSQL server..."
  sleep 1
done
python3 manage.py makemigrations runner
python3 manage.py migrate

# Wait for RabbitMQ
while ! nc -z cno_im_rabbit 5672; do
  echo "Waiting for RabbitMQ server..."
  sleep 1
done

# Start supervisor service
supervisord -c /etc/supervisor/supervisord.conf

# Makes services start on system start
update-rc.d supervisor defaults

# Completed
echo "Initialization completed."
tail -f /dev/null
