import unittest
import argparse
from unittest.mock import patch
from parameterized import parameterized
from io import StringIO
from rss_consumer import main

class TestClientInitialization(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.parser = argparse.ArgumentParser(description="Test client initialization")
        cls.parser.add_argument('-b', dest="bootstrap_servers", required=False, default="localhost:9092",
                        help="Bootstrap broker(s) (host[:port])")
        cls.parser.add_argument('-s', dest="schema_registry", required=False, default="localhost:8081",
                        help="Schema Registry (http(s)://host[:port]")
        cls.parser.add_argument('-t', dest="topic", default="test_topic",
                        help="Topic name")
        cls.parser.add_argument('-g', dest="group", default="test_group",
                        help="Consumer group")

    @parameterized.expand([
        ({'bootstrap_servers': 'localhost:9092', 'schema_registry': 'localhost:8081', 'topic': 'test_topic', 'group': 'test_group'},),
        ({'bootstrap_servers': '127.0.0.1:9092', 'schema_registry': '127.0.0.1:8081', 'topic': 'test_topic', 'group': 'test_group'},),
    ])
    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', side_effect=["image"])
    @patch('rss_consumer.download_blob', return_value="test_image")
    @patch('rss_consumer.model_inference')
    def test_client_initialization(self, args, mock_stdout, mock_input, mock_download_blob, mock_model_inference):
        main(self.parser.parse_args([]))

        # Check if the expected variables are not None
        self.assertIsNotNone(args.bootstrap_servers)
        self.assertIsNotNone(args.schema_registry)
        self.assertIsNotNone(args.topic)
        self.assertIsNotNone(args.group)

        # Check if the expected messages are printed to the console
        expected_output = "Client: "
        self.assertIn(expected_output, mock_stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
