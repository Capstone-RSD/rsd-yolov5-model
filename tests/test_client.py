import unittest

class TestClient(unittest.TestCase):

    def test_client_initialization(self):
        # initialize the client
        client = google.protobuf.json_format.Parse(msg.value(),rssClient,ignore_unknown_fields=True)
        
        # check if the client is not None
        self.assertIsNotNone(client)

        # check if the client has the required attributes
        self.assertTrue(hasattr(client, "blobs"))
        self.assertTrue(len(client.blobs) > 0)

        # check if the client blob has the required attributes
        blob = client.blobs[0]
        self.assertTrue(hasattr(blob, "blob_url"))

    def test_model_inference(self):
        # set the required parameters
        model = model
        imgsz = 224
        stride = 32
        pt = "cpu"
        device = "cpu"
        conf_thres = 0.5
        iou_thres = 0.5

        # download the blob and run the model inference
        image_blob = client.blobs[0]
        if image_blob.image == "image":
            img = download_blob(image_blob.blob_url)
        else:
            self.fail("Video blob type expected")

        if img is not None:
            model_inference(imagePath=download_blob(image_blob.blob_url), model=model, imgsz=imgsz, stride=stride,
            pt=pt, device=device, conf_thres=conf_thres, iou_thres=iou_thres)

if __name__ == '__main__':
    unittest.main()
