"""
This module contains tests for the rss_consumer module.
"""
import argparse
import logging
import os
from dotenv import load_dotenv, find_dotenv
from confluent_kafka import Consumer, Producer
from google.protobuf.json_format import Parse
import torch

from yolov5.models.common import DetectMultiBackend
from yolov5.utils.general import check_img_size
from yolov5.utils.torch_utils import select_device
from generated.rss_schema_pb2 import RSSPayload

from rss_consumer_neo4j import JsonToNeo4j

from rss_consumer_firebase import download_blob
from rss_consumer_yolov5 import model_inference



# Create logger and set the logging level to INFO
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - (%(filename)s:%(funcName)s) %(levelname)s %(name)s:\t\t%(message)s",
)

# Load environment variables
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

# pylint: disable=too-many-locals
def main(args):
    """
    Consumes and performs a model inference before publishing its results to a Kafka topic
    """

    topic = args.topic

    # Set up Kafka consumer configuration
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

    # Set up Kafka producer configuration
    producer_conf = {
        "bootstrap.servers": args.bootstrap_servers,
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms": "PLAIN",
        "sasl.username": args.cluster_key,
        "sasl.password": args.cluster_secret,
    }

    producer = Producer(producer_conf)
    consumer = Consumer(consumer_conf)
    consumer.subscribe([topic])

    # Set up YOLOv5 configuration
    # pylint: disable=no-member
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
    stride, pt = model.stride, model.pt
    imgsz = check_img_size(imgsz, s=stride)  # check image size

    neo4j = JsonToNeo4j(args.db_uri, args.db_username, args.db_password)
    logger.info("Waiting for events...")
    while True:
        try:
            producer.poll(0.0)
            # SIGINT can't be handled when polling, limit timeout to 1 second.
            # Polling for incoming messages
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            logger.debug("Consumed message: {}".format(msg.value()))

            rss_publisher(producer,msg="Data processing - Event consumed on RSS Service")

            # Deserialize incoming message
            rssPayload = RSSPayload()
            client = Parse(msg.value(), rssPayload.client, ignore_unknown_fields=True)

            if client is not None and len(client.blobs) > 0:

                # downloads the blob prior to inferencing
                image_blob = client.blobs[0]

                damagePayload=[]
                boundedbox_image_url=""
                if image_blob.image == "image":
                    try:
                        # img = download_blob(image_blob.blob_url)
                        logger.debug("Blob Url: {}".format(image_blob.blob_url))
                        damagePayload,boundedbox_image_url = model_inference(
                            imagePath=download_blob(image_blob.blob_url),
                            model=model,
                            imgsz=imgsz,
                            stride=stride,
                            pt=pt,
                            device=device,
                            conf_thres=conf_thres,
                            iou_thres=iou_thres,
                        )
                        logger.debug("Boundedbox Blob Url: {}".format(boundedbox_image_url))

                    except ValueError:
                        logger.error("Image blob type expected, received Video blob instead")


                rss_publisher(producer,msg="Data processing - Event processed on RSS Service")

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

                    rss_publisher(producer,msg="Data processing - Payload stored on Neo4J Database and available on dashboard")

                else:
                    logger.debug("No damage detected.")
            else:
                continue
        except KeyboardInterrupt:
            break

    # Releasing resources and stopping application quietly
    consumer.close()
    # Wait for all messages in the Producer queue to be delivered
    producer.flush()
    neo4j.close()
    logger.info("Flushing records and releasing resources...")

def rss_publisher(producer,msg:str):
    """
    Handles publishing the status events to Kafka
    """
    producer.produce(
                            topic="rss_pres_topic",
                            partition=0,
                            key="status",
                            value="Stage: {}".format(msg),
                            on_delivery=delivery_report,
                        )

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
