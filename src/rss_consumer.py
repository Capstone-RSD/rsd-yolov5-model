import argparse
import logging
from dotenv import load_dotenv, find_dotenv
import os
import datetime
import json
from confluent_kafka import Consumer, Producer
from generated.rss_schema_pb2 import Client, RSSPayload
from confluent_kafka.serialization import (
    StringSerializer,
    SerializationContext,
    MessageField,
)
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.protobuf import ProtobufSerializer

from google.protobuf.json_format import MessageToJson, Parse
from rss_consumer_neo4j import JsonToNeo4j

from rss_consumer_firebase import download_blob
from rss_consumer_yolov5 import model_inference

import sys
from pathlib import Path

import torch
import torch.backends.cudnn as cudnn

from yolov5.models.common import DetectMultiBackend
from yolov5.utils.general import check_img_size
from yolov5.utils.torch_utils import select_device

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - (%(filename)s:%(funcName)s) %(levelname)s %(name)s:\t%(message)s",
)
load_dotenv(find_dotenv())


def delivery_report(err, msg):
    """
    Reports the failure or success of a message delivery.
    Args:
        err (KafkaError): The error that occurred on None on success.
        msg (Message): The message that was produced or failed.
    """

    if err is not None:
        logger.warning("Delivery failed for record {}: {}".format(msg.key(), err))
        return
    logger.info(
        "Record {} successfully produced to {} [{}] at offset {}".format(
            msg.key(), msg.topic(), msg.partition(), msg.offset()
        )
    )


def main(args):

    topic = args.topic

    # schema_registry_conf = {
    #     "url": args.schema_registry,
    #     "basic.auth.user.info":os.getenv('SR_API_KEY')+":"+os.getenv('SR_API_SECRET'),
    # }

    # schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    # protobuf_serializer = ProtobufSerializer(
    #     RSSPayload, schema_registry_client, {"use.deprecated.format": False}
    # )

    # producer_conf = {
    #     "bootstrap.servers": args.bootstrap_servers,
    #     "security.protocol": "SASL_SSL",
    #     "sasl.mechanisms": "PLAIN",
    #     "sasl.username": args.cluster_key,
    #     "sasl.password": args.cluster_secret,
    # }

    # producer = Producer(producer_conf)

    consumer_conf = {
        "bootstrap.servers": args.bootstrap_servers,
        "group.id": args.group,
        "auto.offset.reset": "earliest",
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms": "PLAIN",
        "sasl.username": args.cluster_key,
        "sasl.password": args.cluster_secret,
        #  "consumer_timeout_ms":1000,
        "session.timeout.ms": 45000,
    }

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    weights = os.path.abspath("best.pt")
    data = os.path.abspath("data.yaml")
    conf_thres = 0.4
    iou_thres = 0.45
    imgsz = [416, 416]

    torch.no_grad()
    # Load model
    device = select_device(device)
    model = DetectMultiBackend(weights, device=device, dnn=False, data=data, fp16=False)
    stride, names, pt = model.stride, model.names, model.pt
    imgsz = check_img_size(imgsz, s=stride)  # check image size

    consumer = Consumer(consumer_conf)
    consumer.subscribe([topic])

    neo4j = JsonToNeo4j(args.db_uri, args.db_username, args.db_password)
    while True:
        try:
            # Serve on_delivery callbacks from previous calls to produce()
            # producer.poll(0.0)
            # SIGINT can't be handled when polling, limit timeout to 1 second.
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            logger.info("Waiting for events...")
            logger.debug("Consumed message: {}".format(msg.value()))
            rssPayload = RSSPayload()
            client = Parse(msg.value(), rssPayload.client, ignore_unknown_fields=True)
            if client is not None:
                # logs out hte client
                if len(client.blobs) < 1:
                    
                    continue

                else:
                    
                    logger.debug("Client blob_url: {}".format(client.blobs[0].blob_url))

                    # downloads the blob prior to inferencing
                    image_blob = client.blobs[0]

                    if image_blob.image == "image":
                        img = download_blob(image_blob.blob_url)
                    else:
                        print("Video blob type expected")

                    damagePayload, boundedbox_image_url = model_inference(
                        imagePath=download_blob(image_blob.blob_url),
                        model=model,
                        imgsz=imgsz,
                        stride=stride,
                        pt=pt,
                        device=device,
                        conf_thres=conf_thres,
                        iou_thres=iou_thres,
                    )

                    if len(damagePayload) > 0:
                        js_obj = {
                            "name": client.name,
                            "id": client.id,
                            "email": client.email,
                            "latitude": client.damageLocation.lat_lng.latitude,
                            "longitude": client.damageLocation.lat_lng.longitude,
                            "speed": client.speed,
                            "blob_url": client.blobs[0].blob_url,
                            "boundedbox_image_url": boundedbox_image_url,
                            # "datetime_created": client.blobs[0].datetime_created,
                            # "type": client.blobs[0].blob_type,
                            "damagePayload": damagePayload,
                        }

                        logger.debug(js_obj)

                        neo4j.create_nodes(json_data=js_obj)

                        logger.info(
                            "Producing records to topic {}. ^C to exit.".format("rss_topic_test")
                        )

                        rssPayload.client.name="Slim Shady"
                        # rssPayload.client=client

                        # producer.produce(
                        #     topic="rss_topic_test",
                        #     partition=0,
                        #     key="payload",
                        #     value=protobuf_serializer(
                        #         rssPayload, SerializationContext(topic, MessageField.VALUE)
                        #     ),
                        #     on_delivery=delivery_report,
                        # )

                    else:
                        logger.debug("No damage detected.")

        except KeyboardInterrupt:
            break

    # producer.flush()
    consumer.close()
    neo4j.close()
    logger.info("Flushing records and releasing resources...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RSS Consumer ML Service")
    parser.add_argument(
        "-b",
        dest="bootstrap_servers",
        required=False,
        help="Bootstrap broker(s) (host[:port])",
        default="pkc-4rn2p.canadacentral.azure.confluent.cloud:9092",
    )
    parser.add_argument(
        "-s",
        dest="schema_registry",
        required=False,
        help="Schema Registry (http(s)://host[:port]",
        default="https://psrc-30dr2.us-central1.gcp.confluent.cloud:443",
    )
    parser.add_argument("-t", dest="topic", default="rss_topic", help="Topic name")
    parser.add_argument(
        "-g", dest="group", default="example_serde_protobuf", help="Consumer group"
    )
    parser.add_argument(
        "--cluster_key",
        dest="cluster_key",
        default=os.getenv("CLUSTER_API_KEY"),
        help="Cluster API Key",
    )
    parser.add_argument(
        "--cluster_secret",
        dest="cluster_secret",
        default=os.getenv("CLUSTER_API_SECRET"),
        help="Cluster API Secret",
    )

    parser.add_argument(
        "--neo4j_db_password",
        dest="db_password",
        default=os.getenv("NEO4J_DB_PASSWORD"),
        help="Neo4j DB Password",
    )
    parser.add_argument(
        "--neo4j_db_username",
        dest="db_username",
        default=os.getenv("NEO4J_DB_USERNAME"),
        help="Neo4j DB Username",
    )
    parser.add_argument(
        "--neo4j_db_uri",
        dest="db_uri",
        default=os.getenv("NEO4J_DB_URI"),
        help="Neo4j DB Uri",
    )

    main(parser.parse_args())
