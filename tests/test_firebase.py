import unittest

from src.rss_consumer_firebase import download_blob

# https://youtu.be/-PHBRzL80Lk
class TestFirebase(unittest.TestCase):
    def test_firebase(self):
        """
        Test that our function can get an image from firebase storage
        """
        result=download_blob("https://firebasestorage.googleapis.com/v0/b/rss-client-21d3b.appspot.com/o/users%2FLVCRRtv1pgeCDusQC6lC9SrSSlp2%2Fuploads%2F1677022217697261.jpg?alt=media&token=9eb91437-0cca-4108-a486-71283f85bb31")

        self.assertNotEqual(result, False)

    def test_decrement(self):
        self.assertEqual(4,4)

if __name__ == '__main__':
    unittest.main()
