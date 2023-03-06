import unittest
from generated.rss_schema_pb2 import Client, RSSPayload
import argparse
from confluent_kafka import Consumer, Producer
from dotenv import load_dotenv, find_dotenv
import os

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

    def test_client_initialization(self):
        # Create a Client object from a serialized message
        client = Client()
        client.ParseFromString(msg.value())

        # Check if the client is not None
        self.assertIsNotNone(client)

        # Check if the client has the required attributes
        self.assertTrue(hasattr(client, "blobs"))
        self.assertTrue(len(client.blobs) > 0)

        # Check if the client blob has the required attributes
        blob = client.blobs[0]
        self.assertTrue(hasattr(blob, "blob_url"))

    def test_model_inference(self):
        # Set the required parameters
        model = model
        imgsz = 224
        stride = 32
        pt = "cpu"
        device = "cpu"
        conf_thres = 0.5
        iou_thres = 0.5

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
    args = parser.parse_args()
    TestClient.topic = args.topic
    unittest.main()
