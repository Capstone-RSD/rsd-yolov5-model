FROM pytorch/pytorch:latest

WORKDIR /workspace
COPY . /workspace

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

# Setup the notebook kernel
RUN pip install -U ipykernel && \
    pip install -r requirements.txt


CMD [ "python", "src/rss_consumer.py" ]
