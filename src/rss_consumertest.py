"""
This module contains tests for the rss_consumer module.
"""

import argparse
import logging

import torch
from dotenv import load_dotenv, find_dotenv

from confluent_kafka import Consumer

from google.protobuf import json_format

from yolov5.models.common import DetectMultiBackend
from yolov5.utils.general import check_img_size
from yolov5.utils.torch_utils import select_device

from generated.rss_schema_pb2 import Client

from rss_consumer_firebase import download_blob
from rss_consumer_yolov5 import model_inference

# Set the logging level to INFO
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv(find_dotenv())

# pylint: disable=too-many-locals
def main(args):
    """
    Main function that subscribes to a Kafka topic and processes incoming messages
    """
    topic = args.topic

    # Set up Kafka consumer configuration
    consumer_conf = {
        'bootstrap.servers': args.bootstrap_servers,
        'group.id': args.group,
        'auto.offset.reset': "earliest",
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms": "PLAIN",
        "sasl.username": args.cluster_key,
        "sasl.password": args.cluster_secret,
        "session.timeout.ms": 45000
    }

    # Set up YOLOv5 configuration
    # pylint: disable=no-member
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    weights = '../best.pt'
    data = 'pavement-cracks-1/data.yaml'
    conf_thres = 0.4
    iou_thres = 0.45
    imgsz = [416, 416]

    torch.no_grad()

    # Load model
    device = select_device(device)
    model = DetectMultiBackend(weights, device=device, dnn=False, data=data, fp16=False)
    stride, pt_file = model.stride, model.pt
    imgsz = check_img_size(imgsz, s=stride)  # check image size

    # Set up Kafka consumer
    consumer = Consumer(consumer_conf)
    consumer.subscribe([topic])

    while True:
        try:
            # Poll for incoming messages
            msg = consumer.poll(1.0)
            if msg is None:
                continue

            # Deserialize incoming message
            rss_client = Client()
            client = json_format.Parse(msg.value(), rss_client, ignore_unknown_fields=True)
            if client is not None:
                logging.info("Incoming message: %s", client)
                logging.info("Incoming message blob_url: %s", client.blobs[0].blob_url)

                # Download the blob prior to inferencing
                image_blob = client.blobs[0]
                if image_blob.image == "image":
                    img = download_blob(image_blob.blob_url)
                else:
                    logging.error("Video blob type expected")

                if img is not None:
                    model_inference(imagePath=download_blob(image_blob.blob_url),
                                    model=model, imgsz=imgsz, stride=stride,
                                    pt=pt_file, device=device, conf_thres=conf_thres,
                                    iou_thres=iou_thres)

        except KeyboardInterrupt:
            break

    # Close Kafka consumer
    consumer.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bootstrap-servers', type=str, default='localhost:9092',
                        help='Bootstrap server URL')
    parser.add_argument('--group', type=str, default='my-group',
                        help='Consumer group ID')
    parser.add_argument('--cluster-key', type=str, required=True,
                        help='Cluster API key')
