import argparse
from dotenv import load_dotenv,find_dotenv
import os
from confluent_kafka import Consumer
# import rss_payload_pb2 as RSSPayload
# import rss_client_pb2 as RSSClient

from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry.protobuf import ProtobufDeserializer

from confluent_kafka.schema_registry import SchemaRegistryClient
# payload = RSSPayload.tyRSSPayload()
# payload.damage_type=

from rss_consumer_firebase import download_blobmain

#................
import os
import sys
from pathlib import Path

import torch
import torch.backends.cudnn as cudnn
#...........
ROOT = '/Road/yolov5/'
if str(ROOT) not in sys.path:
        sys.path.append(str(ROOT))  # add ROOT to PATH
    #ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from yolov5.models.common import DetectMultiBackend
from yolov5.utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams
from yolov5.utils.general import (LOGGER, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
             increment_path, non_max_suppression, print_args, scale_boxes, strip_optimizer, xyxy2xywh)
from yolov5.utils.plots import Annotator, colors, save_one_box
from yolov5.utils.torch_utils import select_device, time_sync
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
                    #  "consumer_timeout_ms":1000,
                     "session.timeout.ms":45000}


# ...............................................................................................
    device=torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    weights='best.pt'
    data='pavement-cracks-1/data.yaml'
    conf_thres=0.4
    iou_thres=0.45
    imgsz=[416,416]

    torch.no_grad()
    # Load model
    device = select_device(device)
    model = DetectMultiBackend(weights, device=device, dnn=False, data=data, fp16=False)
    stride, names, pt = model.stride, model.names, model.pt
    imgsz = check_img_size(imgsz, s=stride)  # check image size
# ................................................................................................


    consumer = Consumer(consumer_conf)
    consumer.subscribe([topic])

    # while True:
    #     try:
    #         # SIGINT can't be handled when polling, limit timeout to 1 second.
    #         msg = consumer.poll(1.0)
    #         if msg is None:
    #             continue

            # rssClient = protobuf_deserializer(msg.value(), SerializationContext(topic, MessageField.VALUE))

            # if rssClient is not None:
            #     print("User record {}:\n"
            #           "\tname: {}\n"
            #           "\tfavorite_number: {}\n"
            #           "\tfavorite_color: {}\n"
            #           .format(msg.key(), rssClient.name,
            #                   rssClient.id,
            #                   rssClient.email))

            #..................................................................................................

    import numpy as np
    from yolov5.utils.augmentations import letterbox
    imagePath="us14--38-_jpg.rf.7067e4519392d181489b82ca5f8586c4.jpg"
    img0 = cv2.imread(imagePath)

    # source='pavement-cracks-1/test/images'
    # dataset = LoadImages(source, img_size=imgsz, stride=stride, auto=pt)
    # im0s = im0s in dataset

    # Padded resize
    img = letterbox(img0, imgsz, stride, auto=pt)[0]

    # Convert
    img = img.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
    img = np.ascontiguousarray(img)

    bs = 1  # batch_size

    # Run inference
    model.warmup(imgsz=(1 if pt else bs, 3, *imgsz))  # warmup
    seen, windows, dt = 0, [], [0.0, 0.0, 0.0]
    t1 = time_sync()
    im = torch.from_numpy(img).to(device).cuda(device)
    im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
    im /= 255  # 0 - 255 to 0.0 - 1.0
    if len(im.shape) == 3:
        im = im[None]  # expand for batch dim
    t2 = time_sync()
    dt[0] += t2 - t1

    # Inference
    #visualize = increment_path(save_dir / Path(path).stem, mkdir=True) if visualize else False
    pred = model(im, augment=None, visualize=False)
    t3 = time_sync()
    dt[1] += t3 - t2

    # NMS
    pred = non_max_suppression(pred, conf_thres, iou_thres, None, False, max_det=1000)
    dt[2] += time_sync() - t3

    # Second-stage classifier (optional)
    # pred = utils.general.apply_classifier(pred, classifier_model, im, im0s)
    seen += 1
    det=pred[0]
    if len(det):
        # Rescale boxes from img_size to im0 size
        pred2=scale_boxes(im.shape[2:], det[:, :4], img0.shape).round()
        print(det.shape)
        print('box: '+str(np.array(pred2.cpu())))
        print('class: '+str(det[:,-1].cpu()))
        print('confidence: '+str(np.array(det[:,-2].cpu())))
        #break;
    #..................................................................................................

# except KeyboardInterrupt:
#     break

# consumer.close()


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