"""Run with .venv/bin/python checks/verify_upgrade.py /path/to/single-face.jpg.
Uses a supplied fixture; writes only to a temporary recording directory.
"""
import csv
import io
import json
import sys
import os
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
import numpy as np
os.environ.setdefault("FACE_LAB_MODEL_DIR", str(Path(__file__).resolve().parents[1]/"models"))
import face_lab.app as application

client=application.app.test_client()
assert client.get('/health').json['version']==2
assert client.get('/').status_code==200
assert client.get('/static/app.js').status_code==200
assert client.post('/analyze').status_code==400
assert client.post('/save',headers={'Origin':'https://example.invalid'}).status_code==403
assert client.post('/save',data={'video':(io.BytesIO(b'test'),'video.webm'),'metrics':'[{"seconds":0,"face":true,"mode":"detail","models":{"baseline":[]}}]'}).status_code==400
assert client.post('/analyze',data={'mode':'bad'}).status_code==400
blank=cv2.imencode('.jpg',np.zeros((480,640,3),np.uint8))[1].tobytes()
r=client.post('/analyze',data={'frame':(io.BytesIO(blank),'blank.jpg')})
assert r.status_code==200 and r.json['face'] is False and r.json['models']=={} and r.json['au'] is None
image=cv2.imread(sys.argv[1]);assert image is not None
encoded=cv2.imencode('.jpg',image)[1].tobytes()
results=[]
for mode in ['baseline','compare','detail']:
 response=client.post('/analyze',data={'frame':(io.BytesIO(encoded),'face.jpg'),'mode':mode})
 assert response.status_code==200,response.data
 data=response.json;assert data['face'];assert set(data['models'])==({'baseline'} if mode=='baseline' else {'baseline','emotieff'})
 for key,model in data['models'].items():
  assert len(model['scores'])==(7 if key=='baseline' else 8)
  assert abs(sum(model['scores'])-1)<1e-6
 if mode=='detail':
  assert data['au'],data
  assert len(data['au']['intensity'])==12 and len(data['au']['presence'])==12
  assert all(0<=v<=5 for v in data['au']['intensity'].values())
 else:assert data['au'] is None
 results.append({'seconds':len(results),**data})
 print(mode,data['total_ms'],'ms',flush=True)
# A subsequent empty frame must not reuse the last face or AU results.
r=client.post('/analyze',data={'frame':(io.BytesIO(blank),'blank.jpg')})
assert r.json['au'] is None and r.json['models']=={}
results.append({'seconds':3,**r.json})
with tempfile.TemporaryDirectory() as tmp:
 root=application.ROOT;application.ROOT=Path(tmp)
 try:
  response=client.post('/save',data={'video':(io.BytesIO(b'test-only'),'video.webm'),'metrics':json.dumps(results)})
  assert response.status_code==200,response.data
  folder=Path(response.json['path']);rows=list(csv.reader((folder/'predictions.csv').open(encoding='utf-8-sig')))
  assert len(rows)==5 and all(len(row)==len(rows[0]) for row in rows)
  assert len(json.loads((folder/'analysis.json').read_text())['samples'])==4
  for name in ['video.webm','predictions.csv','analysis.json']:
   assert client.get('/recordings/'+folder.name+'/'+name).status_code==200
  assert client.get('/recordings/'+folder.name+'/README.txt').status_code==404
 finally:application.ROOT=root

application.engines.landmarker.close()
print('PASS: real models, output shapes, missing face, modes, CSV/JSON and recording routes')
