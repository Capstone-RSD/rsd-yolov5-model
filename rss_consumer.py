

import argparse
from dotenv import load_dotenv,find_dotenv
import os
from confluent_kafka import Consumer
import rss_payload_pb2 as RSSPayload
import rss_client_pb2 as RSSClient

from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry.protobuf import ProtobufDeserializer

from confluent_kafka.schema_registry import SchemaRegistryClient


# def configure():
load_dotenv(find_dotenv())

def main(args):

    topic = args.topic

    schema_registry_conf = {'url': args.schema_registry,
                            "basic.auth.credentials.source":"USER_INFO",
                            "basic.auth.user.info":os.getenv('SR_API_KEY')+":"+os.getenv('SR_API_SECRET'),
                            'use.deprecated.format': False
                            }

    # schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    # protobuf_deserializer = ProtobufDeserializer(RSSClient.Client,
    #                                              schema_registry_conf)

    consumer_conf = {'bootstrap.servers': args.bootstrap_servers,
                     'group.id': args.group,
                     'auto.offset.reset': "earliest",
                     "security.protocol":"SASL_SSL",
                     "sasl.mechanisms":"PLAIN",
                     "sasl.username":os.getenv("CLUSTER_API_KEY"),
                     "sasl.password":os.getenv("CLUSTER_API_SECRET"),
                     "session.timeout.ms":45000}


    consumer = Consumer(consumer_conf)
    consumer.subscribe([topic])

    while True:
        try:
            # SIGINT can't be handled when polling, limit timeout to 1 second.
            msg = consumer.poll(1.0)
            if msg is None:
                continue

            print(msg.value());

            # rssClient = protobuf_deserializer(msg.value(), SerializationContext(topic, MessageField.VALUE))

            # if rssClient is not None:
            #     print("User record {}:\n"
            #           "\tname: {}\n"
            #           "\tfavorite_number: {}\n"
            #           "\tfavorite_color: {}\n"
            #           .format(msg.key(), rssClient.name,
            #                   rssClient.id,
            #                   rssClient.email))
        except KeyboardInterrupt:
            break

    consumer.close()

    # StopIteration if no message after 1sec
    # KafkaConsumer(consumer_timeout_ms=1000)

    # Subscribe to a regex topic pattern
    # consumer = KafkaConsumer()
    # consumer.subscribe(pattern='^awesome.*')

    # Use multiple consumers in parallel w/ 0.9 kafka brokers
    # typically you would run each on a different server / process / CPU
    # consumer1 = KafkaConsumer('my-topic',
    #                         group_id='my-group',
    #                         bootstrap_servers='my.server.com')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="ProtobufDeserializer example")
    parser.add_argument('-b', dest="bootstrap_servers", required=False,
                        help="Bootstrap broker(s) (host[:port])", default="pkc-3w22w.us-central1.gcp.confluent.cloud:9092")
    parser.add_argument('-s', dest="schema_registry", required=False,
                        help="Schema Registry (http(s)://host[:port]",default="https://psrc-mw0d1.us-east-2.aws.confluent.cloud")
    parser.add_argument('-t', dest="topic", default="rss_topic",
                        help="Topic name")
    parser.add_argument('-g', dest="group", default="example_serde_protobuf",
                        help="Consumer group")

    main(parser.parse_args())