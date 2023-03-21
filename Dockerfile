# FROM pytorch/pytorch:latest
FROM bitnami/pytorch:1.13.0-debian-11-r16


# Set up new user
# RUN useradd -ms /bin/bash developer
# USER developer
# WORKDIR /home/developer
WORKDIR /app

COPY . /app
# RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y


# Setup the notebook kernel
# RUN pip install -U ipykernel && \
RUN pip install -r requirements-prod.txt


CMD [ "python", "src/rss_consumer.py" ]
