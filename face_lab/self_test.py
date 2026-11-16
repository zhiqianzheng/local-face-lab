"""Offline runtime check using synthetic inputs only, without opening the camera."""
import json
import numpy as np
import mediapipe as mp
from . import __version__
from .engines import Engines

def run():
    engine=Engines()
    try:
        blank=np.zeros((480,640,3),np.uint8)
        result=engine.analyze(blank,'baseline')
        assert not result['face']
        engine.baseline._model.setInput(np.zeros((1,3,112,112),np.float32),'data')
        output=engine.baseline._model.forward(['label'])[0]
        assert output.size==7 and np.isfinite(output).all()
        output=engine.emoti.run(None,{'input':np.zeros((1,3,224,224),np.float32)})[0]
        assert output.size==8 and np.isfinite(output).all()
        feature=engine.encoder.run(None,{'image':np.zeros((1,3,224,224),np.float32)})[0].reshape(1,512)
        for head in (engine.intensity,engine.presence):
            output=head.run(None,{'feature':feature})[0]
            assert output.size==12 and np.isfinite(output).all()
        mesh=engine.landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB,data=blank))
        assert mesh.face_landmarks==[]
        print(json.dumps({'ok':True,'version':__version__,'checks':['YuNet','MobileFaceNet','EmotiEffLib','LibreFace encoder/intensity/presence','MediaPipe native library']},ensure_ascii=False),flush=True)
    finally:
        engine.landmarker.close()
