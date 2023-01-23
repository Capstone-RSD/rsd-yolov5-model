# FROM pytorch/pytorch:1.13.1-cuda11.6-cudnn8-runtime
FROM pytorch/pytorch:latest
# FROM python:3-alpine3.9
# FROM  bitnami/python:latest


WORKDIR /workspace
COPY . /workspace

# Setup the notebook kernel
RUN pip install -U ipykernel

RUN pip install -r requirements.txt && \
    pip install google-api-python-client python-dotenv
    # apt-get update && apt install git -y && \
