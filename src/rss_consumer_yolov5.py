import torch
import torch.backends.cudnn as cudnn

from yolov5.models.common import DetectMultiBackend
from yolov5.utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams
from yolov5.utils.general import (LOGGER, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
             increment_path, non_max_suppression, print_args, scale_boxes, strip_optimizer, xyxy2xywh)
from yolov5.utils.plots import Annotator, colors, save_one_box
from yolov5.utils.torch_utils import select_device, time_sync

import numpy as np
from yolov5.utils.augmentations import letterbox

def model_inference(imagePath, model, imgsz, stride, pt, device, conf_thres, iou_thres):
    img0 = cv2.imread(imagePath)

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
    if len(det):
        # Rescale boxes from img_size to im0 size
        pred2=scale_boxes(im.shape[2:], det[:, :4], img0.shape).round()
        print(det.shape)
        print('box: '+str(np.array(pred2.cpu())))
        print('class: '+str(det[:,-1].cpu()))
        print('confidence: '+str(np.array(det[:,-2].cpu())))