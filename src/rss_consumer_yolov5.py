import torch

from yolov5.utils.general import (cv2,non_max_suppression, scale_boxes)
from yolov5.utils.torch_utils import time_sync

import numpy as np
from yolov5.utils.augmentations import letterbox
from generated.rss_payload_pb2 import DamagePayload

def model_inference(imagePath, model, imgsz, stride, pt, device, conf_thres, iou_thres):
    
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
    im = torch.from_numpy(img).to(device).cuda(device)
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
    if len(det):
        # Rescale boxes from img_size to im0 size
        pred2=scale_boxes(im.shape[2:], det[:, :4], img0.shape).round()
        confidence=np.array(det[:,-2].cpu())
        box=np.array(pred2.cpu())
        classification=np.array(det[:,-1].cpu())
        print(det.shape)
        print('box: '+str(box))
        print('class: '+str(classification))
        print('confidence: '+str(confidence))        

        #Calculate Lenth, Width, and get Class name
        # image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        class_name = ['alligator cracking', 'edge cracking', 'longitudinal cracking', 'patching', 'pothole', 'rutting', 'transverse cracking']
        count = 0
        for x in classification:
            payload = DamagePayload()
            payload.damage_class = class_name[x]
            payload.damage_width = abs(box[count, 0] - box[count, 2])
            payload.damage_length = abs(box[count, 1] - box[count, 3])
            damages_payload.append(payload)
            count=count+1
            print('payload: ', damages_payload)
            #Draw boxes on image
            # cv2.rectangle(image, (box[count, 0], box[count, 1]), (box[count, 2], box[count, 3]), (255,0,0), 2)

    return damages_payload
            