FROM pytorch/pytorch:latest

WORKDIR /workspace
COPY . /workspace

# Setup the notebook kernel
RUN pip install -U ipykernel && \
    pip install -r requirements.txt
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

CMD [ "python", "rss_consumer.py" ]