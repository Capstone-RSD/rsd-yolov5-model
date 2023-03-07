import unittest
from src.generated.rss_schema_pb2 import Client, RSSPayload
import argparse
from src.rss_consumer_firebase import download_blob
from src.rss_consumer_yolov5 import model_inference
from confluent_kafka import Consumer, Producer
from dotenv import load_dotenv, find_dotenv
import os
import requests

load_dotenv(find_dotenv())

class TestClient(unittest.TestCase):
    sasl_username = ""
    sasl_password = ""

    topic = "rss_topic"

    consumer_conf = {'bootstrap.servers': "pkc-v12gj.northamerica-northeast2.gcp.confluent.cloud:9092",
                     'group.id': "example_serde_protobuf",
                     'auto.offset.reset': "earliest",
                     "security.protocol": "SASL_SSL",
                     "sasl.mechanisms": "PLAIN",
                     "sasl.username": sasl_username,
                     "sasl.password": sasl_password,
                     "session.timeout.ms": 45000}
    
    # create a Kafka consumer
    consumer = Consumer(consumer_conf)

    # define a serialized Client object
    client = Client(blobs=[RSSPayload(title="Test Title", description="Test Description", url="http://example.com")])
    serialized_client = client.SerializeToString()

    # set msg variable to the serialized client
    msg = serialized_client

    def test_client_initialization(self):
        # Create a Client object from a serialized message
        client = Client()
        client.ParseFromString(self.msg)

        # Check if the client is not None
        self.assertIsNotNone(client)

        # Check if the client has the required attributes
        self.assertTrue(hasattr(client, "blobs"))
        self.assertTrue(len(client.blobs) > 0)

        # Check if the client blob has the required attributes
        blob = client.blobs[0]
        self.assertTrue(hasattr(blob, "blob_url"))

    @staticmethod
    def download_blob(url):
        # Send an HTTP request to the URL of the image and get the response
        response = requests.get(url)

        # Check if the response was successful (status code 200)
        if response.status_code == 200:
            # Convert the response content to bytes
            content = response.content
            return content
        else:
            # If the response was not successful, return None
            return None

    def test_model_inference(self):

        # Set the required parameters
        model = model
        imgsz = 224
        stride = 32
        pt = "cpu"
        device = "cpu"
        conf_thres = 0.5
        iou_thres = 0.5

        client = RSSPayload

        # Download the blob and run the model inference
        image_blob = client.blobs[0]
        if image_blob.image == "image":
            img = download_blob(image_blob.blob_url)
        else:
            self.fail("Video blob type expected")

        if img is not None:
            model_inference(imagePath=download_blob(image_blob.blob_url), model=model, imgsz=imgsz, stride=stride,
            pt=pt, device=device, conf_thres=conf_thres, iou_thres=iou_thres)

class TestConsumer(unittest.TestCase):
    def test_consumer_consume(self):
        # Create a Kafka consumer
        consumer = Consumer(TestClient.consumer_conf)

        # Subscribe to the test topic
        consumer.subscribe([TestClient.topic])

        # Produce a test message to the topic
        client = Client(blobs=[RSSPayload(blob_url="test_url", image="image")])
        producer_conf = {'bootstrap.servers': TestClient.consumer_conf['bootstrap.servers'],
                          "security.protocol": TestClient.consumer_conf["security.protocol"],
                          "sasl.mechanisms": TestClient.consumer_conf["sasl.mechanisms"],
                          "sasl.username": TestClient.sasl_username,
                          "sasl.password": TestClient.sasl_password}
        producer = Producer(producer_conf)
        producer.produce(TestClient.topic, value=client.SerializeToString())
        producer.flush()

        # Consume the message
        msg = consumer.poll(5.0)

        # Check if the message is not None
        self.assertIsNotNone(msg)

        # Create a Client object from a serialized message
        client = Client()
        client.ParseFromString(msg.value())

        # Check if the client is not None
        self.assertIsNotNone(client)

        # Check if the client has the required attributes
        self.assertTrue(hasattr(client, "blobs"))
        self.assertTrue(len(client.blobs) > 0)

class TestProducer(unittest.TestCase):
    def test_producer_produce(self):
        # Create a Kafka producer
        producer_conf = {'bootstrap.servers': TestClient.consumer_conf['bootstrap.servers'],
                          "security.protocol": TestClient.consumer_conf["security.protocol"],
                          "sasl.mechanisms": TestClient.consumer_conf["sasl.mechanisms"],
                          "sasl.username": TestClient.sasl_username,
                          "sasl.password": TestClient.sasl_password}
        producer = Producer(producer_conf)

        # Produce a test message to the topic
        client = Client(blobs=[RSSPayload(blob_url="test_url", image="image")])
        producer.produce(TestClient.topic, value=client.SerializeToString())
        producer.flush()

        # Create a Kafka consumer
        consumer = Consumer(TestClient.consumer_conf)

        # Subscribe to the test topic
        consumer.subscribe([TestClient.topic])

        # Consume the message
        msg = consumer.poll(5.0)

        # Check if the message is not None
        self.assertIsNotNone(msg)

        # Create a Client object from a serialized message
        client = Client()
        client.ParseFromString(msg.value())

        # Check if the client is not None
        self.assertIsNotNone(client)

        # Check if the client has the required attributes
        self.assertTrue(hasattr(client, "blobs"))
        self.assertTrue(len(client.blobs) > 0)

        # Close the consumer and producer
        consumer.close()
        producer.close()
