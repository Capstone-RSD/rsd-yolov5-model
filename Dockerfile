# FROM pytorch/pytorch:latest
FROM bitnami/pytorch:1.13.0-debian-11-r16

WORKDIR /app

COPY . /app
# RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

RUN pip install -r requirements-prod.txt && ls /app/src && pwd

# CMD [ "python", "-h" ]
CMD ["sleep", "1d"]
