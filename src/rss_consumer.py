import argparse
import logging
from dotenv import load_dotenv,find_dotenv
import os
import datetime
import json
from confluent_kafka import Consumer, Producer
from generated.rss_schema_pb2 import Client, RSSPayload
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.protobuf import ProtobufSerializer

from google.protobuf.json_format import MessageToJson,Parse
from rss_consumer_neo4j import JsonToNeo4j

from rss_consumer_firebase import download_blob
from rss_consumer_yolov5 import model_inference

import sys
from pathlib import Path

import torch
import torch.backends.cudnn as cudnn

ROOT = '/Road/yolov5/'
if str(ROOT) not in sys.path:
        sys.path.append(str(ROOT))  # add ROOT to PATH
    #ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from yolov5.models.common import DetectMultiBackend
from yolov5.utils.general import check_img_size
from yolov5.utils.torch_utils import select_device

load_dotenv(find_dotenv())

def delivery_report(err, msg):
    """
    Reports the failure or success of a message delivery.
    Args:
        err (KafkaError): The error that occurred on None on success.
        msg (Message): The message that was produced or failed.
    """

    if err is not None:
        print("Delivery failed for User record {}: {}".format(msg.key(), err))
        return
    print('User record {} successfully produced to {} [{}] at offset {}'.format(
        msg.key(), msg.topic(), msg.partition(), msg.offset()))

def main(args):

    topic = args.topic

    schema_registry_conf = {'url': args.schema_registry,
                            "basic.auth.credentials.source":"USER_INFO",
                            "basic.auth.user.info":os.getenv('SR_API_KEY')+":"+os.getenv('SR_API_SECRET'),
                            'use.deprecated.format': False
                            }

    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    protobuf_serializer = ProtobufSerializer(RSSPayload,schema_registry_client,
                                                 schema_registry_conf)

    producer_conf = {'bootstrap.servers': args.bootstrap_servers,}

    producer = Producer(producer_conf)

    consumer_conf = {'bootstrap.servers': args.bootstrap_servers,
                     'group.id': args.group,
                     'auto.offset.reset': "earliest",
                     "security.protocol":"SASL_SSL",
                     "sasl.mechanisms":"PLAIN",
                     "sasl.username":args.cluster_key,
                     "sasl.password":args.cluster_secret,
                    #  "consumer_timeout_ms":1000,
                     "session.timeout.ms":45000}

    device=torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    weights=os.path.abspath('best.pt')
    data=os.path.abspath('data.yaml')
    conf_thres=0.4
    iou_thres=0.45
    imgsz=[416,416]

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
            producer.poll(0.0)
            # SIGINT can't be handled when polling, limit timeout to 1 second.
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            # rssClient = protobuf_deserializer(msg.value(), SerializationContext(topic, MessageField.VALUE))
            logging.info(msg.value())
            rssPayload = RSSPayload()
            client = Parse(msg.value(),rssPayload.client,ignore_unknown_fields=True)
            if client is not None:
                # logs out hte client
                if client.blobs[0] is not None:

                    logging.debug("Client blob_url: ",client.blobs[0].blob_url)

                    #downloads the blob prior to inferencing
                    image_blob = client.blobs[0]

                    if image_blob.image == "image":
                        img = download_blob(image_blob.blob_url)
                    else:
                        logging.error("Video blob type expected")

                    damagePayload = model_inference(imagePath=download_blob(image_blob.blob_url), model=model, imgsz=imgsz, stride=stride,
                    pt=pt, device=device, conf_thres=conf_thres, iou_thres=iou_thres)


                    if len(damagePayload) > 0:
                        js_obj = {
                                    "name": client.name,
                                    "id": client.id,
                                    "email": client.email,
                                    "latitude": client.damageLocation.lat_lng.latitude,
                                    "longitude": client.damageLocation.lat_lng.longitude,
                                    "speed": client.speed,
                                    "blob_url": client.blobs[0].blob_url,
                                    # "datetime_created": client.blobs[0].datetime_created,
                                    # "type": client.blobs[0].blob_type,
                                    "damagePayload": damagePayload
                                    }

                        print(js_obj)

                        neo4j.create_nodes(json_data=js_obj)

                        print("Producing records to topic {}. ^C to exit.".format(topic))

                        producer.produce(topic=topic, partition=0,
                             key=None, #string_serializer(str(uuid4())),
                             value=protobuf_serializer(user, SerializationContext(topic, MessageField.VALUE)),
                             on_delivery=delivery_report)

                    else:
                        print("No damage detected.")

        except KeyboardInterrupt:
            break

    consumer.close()
    neo4j.close()

    print("\nFlushing records...")
    producer.flush()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="ProtobufDeserializer example")
    parser.add_argument('-b', dest="bootstrap_servers", required=False,
                        help="Bootstrap broker(s) (host[:port])", default="pkc-v12gj.northamerica-northeast2.gcp.confluent.cloud:9092")
    parser.add_argument('-s', dest="schema_registry", required=False,
                        help="Schema Registry (http(s)://host[:port]",default="https://psrc-mw0d1.us-east-2.aws.confluent.cloud")
    parser.add_argument('-t', dest="topic", default="rss_topic",
                        help="Topic name")
    parser.add_argument('-g', dest="group", default="example_serde_protobuf",
                        help="Consumer group")
    parser.add_argument('--cluster_key', dest="cluster_key", default=os.getenv("CLUSTER_API_KEY"),
                        help="Cluster API Key")
    parser.add_argument('--cluster_secret', dest="cluster_secret", default=os.getenv("CLUSTER_API_SECRET"),
                        help="Cluster API Secret")

    parser.add_argument('--neo4j_db_password', dest="db_password", default=os.getenv("NEO4J_DB_PASSWORD"),
                        help="Neo4j DB Password")
    parser.add_argument('--neo4j_db_username', dest="db_username", default=os.getenv("NEO4J_DB_USERNAME"),
                        help="Neo4j DB Username")
    parser.add_argument('--neo4j_db_uri', dest="db_uri", default=os.getenv("NEO4J_DB_URI"),
                        help="Neo4j DB Uri")

    main(parser.parse_args())