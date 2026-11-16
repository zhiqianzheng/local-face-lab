"""Local inference adapters. Preprocessing follows the respective upstream implementations."""
from pathlib import Path
import time

import cv2
import mediapipe as mp
import numpy as np
import onnxruntime as ort
from PIL import Image
from mediapipe.tasks.python import BaseOptions, vision

from .libreface_alignment import image_align
from .facial_fer_model import FacialExpressionRecog
from .config import model_dir

MODEL_DIR = model_dir()
BASE_LABELS = ['愤怒样表情', '厌恶样表情', '恐惧样表情', '开心样表情', '中性表情', '悲伤样表情', '惊讶样表情']
EMOTI_LABELS = ['愤怒样表情', '轻蔑样表情', '厌恶样表情', '恐惧样表情', '开心样表情', '中性表情', '悲伤样表情', '惊讶样表情']
AU_INTENSITY = [1, 2, 4, 5, 6, 9, 12, 15, 17, 20, 25, 26]
AU_PRESENCE = [1, 2, 4, 6, 7, 10, 12, 14, 15, 17, 23, 24]
AU_NAMES = {1:'内眉上提',2:'外眉上提',4:'眉毛下压',5:'上眼睑上提',6:'脸颊上提',7:'眼睑收紧',9:'皱鼻',10:'上唇上提',12:'嘴角上提',14:'嘴角收紧',15:'嘴角下拉',17:'下巴上提',20:'嘴唇横向拉伸',23:'嘴唇收紧',24:'嘴唇压紧',25:'双唇分开',26:'下颌下落'}
RIGHT_EYE = [33,7,163,144,145,153,154,155,133,246,161,160,159,158,157,173]
LEFT_EYE = [263,249,390,373,374,380,381,382,362,466,388,387,386,385,384,398]
MOUTH = [61,146,91,181,84,17,314,405,321,375,291,185,40,39,37,0,267,269,270,409,78,95,88,178,87,14,317,402,318,324,308,191,80,81,82,13,312,311,310,415]


def session(path):
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    options.log_severity_level = 3
    return ort.InferenceSession(str(path), sess_options=options, providers=['CPUExecutionProvider'])


def softmax(logits):
    values = np.asarray(logits, dtype=np.float64).reshape(-1)
    values = np.exp(values - values.max())
    return values / values.sum()


def classification(logits, labels, started):
    scores = softmax(logits)
    best = int(scores.argmax())
    return {'labels': labels, 'scores': scores.tolist(), 'index': best,
            'label': labels[best], 'ms': round((time.perf_counter()-started)*1000, 2)}


def normalized_rgb(rgb):
    values = np.asarray(rgb, dtype=np.float32) / 255.0
    values = (values - np.array([.485,.456,.406], np.float32)) / np.array([.229,.224,.225], np.float32)
    return np.ascontiguousarray(values.transpose(2,0,1)[None])


class Engines:
    def __init__(self):
        cv2.setNumThreads(2)
        self.detector = cv2.FaceDetectorYN.create(str(MODEL_DIR/'face.onnx'), '', (640,480), .8)
        self.baseline = FacialExpressionRecog(str(MODEL_DIR/'expression.onnx'))
        self.emoti = session(MODEL_DIR/'emotieff-b0.onnx')
        self.encoder = session(MODEL_DIR/'libreface/LibreFace_AU_Encoder.onnx')
        self.intensity = session(MODEL_DIR/'libreface/LibreFace_AU_Intensity.onnx')
        self.presence = session(MODEL_DIR/'libreface/LibreFace_AU_Presence.onnx')
        self.landmarker = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(MODEL_DIR/'face_landmarker.task')),
            running_mode=vision.RunningMode.IMAGE, num_faces=3,
            min_face_detection_confidence=.5, min_face_presence_confidence=.5,
            output_face_blendshapes=False))

    def analyze(self, image, mode='detail'):
        started = time.perf_counter()
        h,w = image.shape[:2]
        self.detector.setInputSize((w,h))
        _,faces = self.detector.detect(image)
        out = {'face':False,'count':0,'mode':mode,'models':{},'au':None,
               'width':w,'height':h}
        if faces is None:
            out['total_ms'] = round((time.perf_counter()-started)*1000,2)
            return out
        face = max(faces,key=lambda f:float(f[2]*f[3]))
        out.update(face=True,count=len(faces),box=[float(v) for v in face[:4]])
        t = time.perf_counter()
        self.baseline._model.setInput(self.baseline._preprocess(image,face[:-1]),'data')
        logits = self.baseline._model.forward(['label'])[0]
        out['models']['baseline'] = classification(logits,BASE_LABELS,t)
        # Preserve the v1 response fields for existing consumers.
        out.update({k:out['models']['baseline'][k] for k in ('label','index','scores')})
        if mode in ('compare','detail'):
            t = time.perf_counter()
            x,y,bw,bh = face[:4]
            x1,y1 = max(0,int(x)),max(0,int(y))
            x2,y2 = min(w,int(x+bw)),min(h,int(y+bh))
            rgb = cv2.cvtColor(image[y1:y2,x1:x2],cv2.COLOR_BGR2RGB)
            tensor = normalized_rgb(cv2.resize(rgb,(224,224)))
            logits = self.emoti.run(None,{'input':tensor})[0]
            out['models']['emotieff'] = classification(logits,EMOTI_LABELS,t)
        if mode == 'detail':
            t = time.perf_counter()
            rgb = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
            result = self.landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB,data=rgb))
            if result.face_landmarks:
                # Match MediaPipe landmarks to the same largest YuNet face.
                center = np.array([face[0]+face[2]/2,face[1]+face[3]/2])
                candidates = [np.array([[p.x,p.y] for p in points],np.float64) for points in result.face_landmarks]
                lm = min(candidates,key=lambda pts:float(np.linalg.norm(pts.mean(0)*[w,h]-center)))
                mesh_center = lm.mean(0)*[w,h]
                if np.linalg.norm(mesh_center-center) > max(face[2],face[3])*.65:
                    out['au_error']='未匹配到同一张脸的面部关键点'
                else:
                    aligned = image_align(Image.fromarray(rgb),lm[LEFT_EYE+RIGHT_EYE+MOUTH],output_size=256)
                    tensor = normalized_rgb(aligned.crop((16,16,240,240)))
                    features = self.encoder.run(None,{'image':tensor})[0].reshape(1,512)
                    intensity = self.intensity.run(None,{'feature':features})[0].reshape(-1)
                    presence = self.presence.run(None,{'feature':features})[0].reshape(-1)
                    out['au'] = {
                        'intensity':{str(k):float(v) for k,v in zip(AU_INTENSITY,np.clip(intensity*5,0,5))},
                        'presence':{str(k):bool(v>=.5) for k,v in zip(AU_PRESENCE,presence)},
                        'presence_scores':{str(k):float(v) for k,v in zip(AU_PRESENCE,presence)},
                        'ms':round((time.perf_counter()-t)*1000,2)}
            else:
                out['au_error']='面部关键点不清晰，暂不输出动作强度'
        out['total_ms']=round((time.perf_counter()-started)*1000,2)
        return out
