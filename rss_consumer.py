

import argparse
from confluent_kafka import Consumer
import rss_payload_pb2 as RSSPayload

from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry.protobuf import ProtobufDeserializer

# payload = RSSPayload.tyRSSPayload()
# payload.damage_type=

# # Required connection configs for Kafka producer, consumer, and admin
# bootstrap.servers=pkc-3w22w.us-central1.gcp.confluent.cloud:9092
# security.protocol=SASL_SSL
# sasl.mechanisms=PLAIN
# sasl.username=X2NUE7DRNVMYC3N6
# sasl.password=eGwV/PP0LGup9JOf1cLZr1mFsoUE9A5a/N4PNJ1hs2A92jw3r4ACGl03VUkMv0fU

# # Best practice for higher availability in librdkafka clients prior to 1.7
# session.timeout.ms=45000

# # Required connection configs for Confluent Cloud Schema Registry
# schema.registry.url=https://psrc-mw0d1.us-east-2.aws.confluent.cloud
# basic.auth.credentials.source=USER_INFO
# basic.auth.user.info=HSDL4TN2PJDJXFZG:faefkwKkj09+FaKnRnPKeXrcunefp5bmC63xlS3DkuMP3IPeLBlpcmQbd1/XDRpl


def main(args):

# To consume latest messages and auto-commit offsets
    consumer = Consumer('rss-topic',
                            group_id='my-group',
                            bootstrap_servers=['pkc-3w22w.us-central1.gcp.confluent.cloud:9092'],
                            security.protocol=SASL_SSL,
                            sasl.mechanisms="PLAIN",
                            sasl.username={{ CLUSTER_API_KEY }},
                            sasl.password={{ CLUSTER_API_SECRET }},
                            session.timeout.ms=45000,
                            schema.registry.url="https://psrc-mw0d1.us-east-2.aws.confluent.cloud"
                            basic.auth.credentials.source=USER_INFO,
                            basic.auth.user.info={{ SR_API_KEY }}:{{ SR_API_SECRET }})

    protobuf_deserializer = ProtobufDeserializer(RSSPayload.RSSPayload,
                                                 {'use.deprecated.format': False})

    consumer_conf = {'bootstrap.servers': args.bootstrap_servers,
                     'group.id': args.group,
                     'auto.offset.reset': "earliest",
                     "security.protocol":"SASL_SSL",
                     "sasl.mechanisms":"PLAIN",
                     "sasl.username":"72N3WVXRKSP3AFSA",
                     "sasl.password":"eGwV/PP0LGup9JOf1cLZr1mFsoUE9A5a/N4PNJ1hs2A92jw3r4ACGl03VUkMv0fU",
                     "session.timeout.ms":45000,
                     "schema.registry.url":"https://psrc-mw0d1.us-east-2.aws.confluent.cloud",
                     "basic.auth.credentials.source":"USER_INFO",
                     "basic.auth.user.info":"HSDL4TN2PJDJXFZG:faefkwKkj09+FaKnRnPKeXrcunefp5bmC63xlS3DkuMP3IPeLBlpcmQbd1/XDRpl"}

    for message in consumer:
        # message value and key are raw bytes -- decode if necessary!
        # e.g., for unicode: `message.value.decode('utf-8')`
        print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                                            message.offset, message.key,
                                            message.value))

    # consume earliest available messages, don't commit offsets
    KafkaConsumer(auto_offset_reset='earliest', enable_auto_commit=False)

    # consume json messages
    KafkaConsumer(value_deserializer=lambda m: json.loads(m.decode('ascii')))

    # consume msgpack
    KafkaConsumer(value_deserializer=msgpack.unpackb)

    # StopIteration if no message after 1sec
    KafkaConsumer(consumer_timeout_ms=1000)

    # Subscribe to a regex topic pattern
    consumer = KafkaConsumer()
    consumer.subscribe(pattern='^awesome.*')

    # Use multiple consumers in parallel w/ 0.9 kafka brokers
    # typically you would run each on a different server / process / CPU
    # consumer1 = KafkaConsumer('my-topic',
    #                         group_id='my-group',
    #                         bootstrap_servers='my.server.com')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="ProtobufDeserializer example")
    parser.add_argument('-b', dest="bootstrap_servers", required=True,
                        help="Bootstrap broker(s) (host[:port])")
    parser.add_argument('-s', dest="schema_registry", required=False,default="pkc-3w22w.us-central1.gcp.confluent.cloud:9092",
                        help="Schema Registry (http(s)://host[:port]")
    parser.add_argument('-t', dest="topic", default="example_serde_protobuf",
                        help="Topic name")
    parser.add_argument('-g', dest="group", default="example_serde_protobuf",
                        help="Consumer group")

    main(parser.parse_args())