# FROM pytorch/pytorch:latest
# FROM bitnami/pytorch:1.13.0-debian-11-r16
# FROM graphcore/pytorch:3.2.0-ubuntu-20.04-20230314
FROM pytorch/torchserve:latest-cpu

WORKDIR /app

COPY . /app
# RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

RUN pip install -r requirements-prod.txt && ls /app/src && pwd

CMD [ "python", "/app/src/rss_consumer.py" ]
# CMD ["sleep", "1d"]
