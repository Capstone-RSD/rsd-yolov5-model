import os
import tempfile
import requests
from unittest import TestCase, mock
from firebase_admin import credentials, initialize_app, storage

def upload_map_to_firebase(file_path):
    """
    Uploads the file to Firebase storage and returns the public URL
    """
    # Initialize Firebase with credentials
    cred = credentials.Certificate("rss-client-21d3b-firebase-private-key.json")
    initialize_app(cred, {'storageBucket': 'rss-client-21d3b.appspot.com'})

    # Get the file name from the path
    file_name = os.path.basename(file_path)

    # Create a bucket object and upload the file
    bucket = storage.bucket()
    blob = bucket.blob("map-markup/"+file_name)
    blob.upload_from_filename(file_path)

    # Make the file publicly accessible
    blob.make_public()

    return blob.public_url


class TestUploadToFirebase(TestCase):

    @mock.patch('firebase_admin.storage.bucket')
    def test_upload_map_to_firebase(self, mock_bucket):
        # Create a temporary file and write some contents to it
        with tempfile.NamedTemporaryFile(delete=False) as fp:
            fp.write(b"test content")

        # Mock the blob object and its methods
        mock_blob = mock.MagicMock()
        mock_bucket.return_value.blob.return_value = mock_blob
        mock_blob.public_url = "https://example.com"

        # Call the function with the temporary file path
        with mock.patch('firebase_admin.credentials.Certificate'):
            result = upload_map_to_firebase(fp.name)

        # Assert that the file was uploaded and a public URL was returned
        self.assertEqual(result, mock_blob.public_url)
        mock_bucket.assert_called_once_with()
        mock_bucket.return_value.blob.assert_called_once_with("map-markup/" + os.path.basename(fp.name))
        mock_blob.upload_from_filename.assert_called_once_with(fp.name)
