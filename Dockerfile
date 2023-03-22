# FROM pytorch/pytorch:latest
FROM bitnami/pytorch:1.13.0-debian-11-r16

WORKDIR /app

COPY . /app
# RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

RUN pip install -r requirements-prod.txt && cd src && ls -al && pwd

CMD [ "python", "src/rss_consumer.py" ]
