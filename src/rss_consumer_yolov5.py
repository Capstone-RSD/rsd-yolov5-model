import torch
import logging
import os
from yolov5.utils.general import (cv2,non_max_suppression, scale_boxes)
from yolov5.utils.torch_utils import time_sync

import numpy as np
from yolov5.utils.augmentations import letterbox
from generated.rss_schema_pb2 import DamagePayload
from rss_consumer_firebase import upload_boundedbox_image_to_firebase

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - (%(filename)s:%(funcName)s) %(levelname)s %(name)s:\t%(message)s",
)

def model_inference(imagePath, model, imgsz, stride, pt, device, conf_thres, iou_thres):
    logger.info("Performing inference...")

    nparr = np.fromstring(imagePath, np.uint8)

    img0 = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

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
    im = torch.from_numpy(img).to(device)#.cuda(device)
    im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
    im /= 255  # 0 - 255 to 0.0 - 1.0
    if len(im.shape) == 3:
        im = im[None]  # expand for batch dim
    t2 = time_sync()
    dt[0] += t2 - t1

    # Inference
    pred = model(im, augment=None, visualize=False)
    t3 = time_sync()
    dt[1] += t3 - t2

    # NMS
    pred = non_max_suppression(pred, conf_thres, iou_thres, None, False, max_det=1000)
    dt[2] += time_sync() - t3

    seen += 1
    det=pred[0]
    damages_payload = []
    boundedbox_image_url = ""
    if len(det):
        # Rescale boxes from img_size to im0 size
        pred2=scale_boxes(im.shape[2:], det[:, :4], img0.shape).round()
        confidence=np.array(det[:,-2].cpu())
        box=np.array(pred2.cpu())
        classification=np.array(det[:,-1].cpu())
        logging.debug(det.shape)
        logging.debug('box: '+str(box))
        logging.debug('class: '+str(classification))
        logging.debug('confidence: '+str(confidence))

        #Calculate Lenth, Width, and get Class name
        class_name = ['alligator cracking', 'edge cracking', 'longitudinal cracking', 'patching', 'pothole', 'rutting', 'transverse cracking']
        count = 0
        # payload = [] # TODO: fix this
        for x in classification:
            x1=int(box[count, 0])
            x2=int(box[count, 2])
            y1=int(box[count, 1])
            y2=int(box[count, 3])
            payload={
                        "damage_class": class_name[int(x)],
                        "damage_width": int(abs(box[count, 0] - box[count, 2])),
                        "damage_length": int(abs(box[count, 1] - box[count, 3]))
                    }

            payload_proto = DamagePayload()
            payload_proto.damage_class = class_name[int(x)]
            payload_proto.damage_width = int(abs(box[count, 0] - box[count, 2]))
            payload_proto.damage_length = int(abs(box[count, 1] - box[count, 3]))

            damages_payload.append(payload)
            count=count+1
            #Draw boxes on image
            img0 = cv2.rectangle(img0, (x1, y1), (x2, y2), (0, 0, 255), 2)

            # For the text background
            # Finds space required by the text so that we can put a background with that amount of width.
            (w, h), _ = cv2.getTextSize(payload["damage_class"], cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)

            # Prints the text.
            img0 = cv2.rectangle(img0, (x1, y1 - 20), (x1 + w, y1), (0, 0, 255), -1)
            img0 = cv2.putText(img0, class_name[int(x)], (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.imwrite('./output.jpg',img0)

            # logger.info("Files and directories in: ", os.listdir())

        boundedbox_image_url = upload_boundedbox_image_to_firebase()
        logger.info("Uploading bounded box image")
        logger.info("Inference successful")
        logger.debug('payload: ', damages_payload)

    return damages_payload, boundedbox_image_url
