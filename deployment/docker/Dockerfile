FROM ubuntu:16.04

# Set working directory
WORKDIR /opt/cognitive-network-optimizer

# Add requirements file
ADD requirements.txt ./requirements.txt

# Update and install packages
RUN apt-get update && apt-get -y install \
    nano \
    netcat \
    python3-dev \
    python3-setuptools \
    python3-pip \
    supervisor \
 && pip3 install -r requirements.txt \
 && apt-get remove -y python3-setuptools python3-pip \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

# Copy source code
COPY . /opt/cognitive-network-optimizer

# Do the rest of the work
RUN rm -rf /etc/supervisor/supervisord.conf \
 && cp deployment/supervisor/supervisord.conf /etc/supervisor/supervisord.conf \
 && cp deployment/supervisor/cognitive-network-optimizer.conf /etc/supervisor/conf.d/cognitive-network-optimizer.conf \
 && chmod +x deployment/docker/run.sh

# Export supervisor port
EXPOSE 3333

# Run script
ENTRYPOINT ["/bin/sh", "-c"]
CMD ["/opt/cognitive-network-optimizer/deployment/docker/run.sh eng"]
