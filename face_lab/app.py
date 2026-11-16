from pathlib import Path
import csv
import math
import json
import threading
import re
from datetime import datetime
from .config import data_dir
from . import __version__

import cv2
import numpy as np
from flask import Flask, jsonify, render_template, request, send_from_directory, abort
from .engines import Engines, BASE_LABELS, EMOTI_LABELS, AU_INTENSITY, AU_PRESENCE, AU_NAMES

ROOT = data_dir()
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024
engines = Engines()
lock = threading.Lock()
LABELS = BASE_LABELS
MODEL_INFO = {
    'baseline': {'name':'原模型 · MobileFaceNet','labels':BASE_LABELS,'file':'models/expression.onnx'},
    'emotieff': {'name':'EmotiEffLib · EfficientNet-B0','labels':EMOTI_LABELS,'file':'models/emotieff-b0.onnx','checkpoint':'enet_b0_8_best_afew'},
    'libreface': {'name':'LibreFace · AU 分析','package':'LibreFace NuGet 2.0.0','intensity_ids':AU_INTENSITY,'presence_ids':AU_PRESENCE},
}

@app.before_request
def check_origin():
    origin = request.headers.get('Origin')
    if request.method == 'POST' and origin and origin != request.host_url.rstrip('/'):
        return jsonify(error='拒绝其他网站发起的本地写入请求'), 403


def validate_rows(rows):
    if not isinstance(rows,list) or len(rows)>10000:
        raise ValueError('Invalid rows')
    def number(value, low=0, high=1e9):
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high:
            raise ValueError('Invalid number')
    for row in rows:
        if not isinstance(row,dict):raise ValueError()
        number(row.get('seconds'),0,65)
        if not isinstance(row.get('face'),bool):raise ValueError()
        if row.get('mode') not in ('baseline','compare','detail'):raise ValueError()
        models=row.get('models',{})
        if not isinstance(models,dict) or set(models)-{'baseline','emotieff'}:raise ValueError()
        for key,m in models.items():
            labels=BASE_LABELS if key=='baseline' else EMOTI_LABELS
            if not isinstance(m,dict) or m.get('label') not in labels:raise ValueError()
            scores=m.get('scores')
            if not isinstance(scores,list) or len(scores)!=len(labels):raise ValueError()
            for score in scores:number(score,0,1)
            number(m.get('ms',0))
        au=row.get('au')
        if au is not None:
            if not isinstance(au,dict):raise ValueError()
            for name,ids in [('intensity',AU_INTENSITY),('presence',AU_PRESENCE),('presence_scores',AU_PRESENCE)]:
                values=au.get(name)
                if not isinstance(values,dict) or set(values)!={str(k) for k in ids}:raise ValueError()
                for value in values.values():
                    if name=='presence':
                        if not isinstance(value,bool):raise ValueError()
                    else:number(value,0,5 if name=='intensity' else 1)
            number(au.get('ms',0))
        number(row.get('total_ms',0))

@app.get('/')
def index():
    return render_template('index.html')

@app.get('/health')
def health():
    return jsonify(ok=True,application="local-face-lab",software_version=__version__,version=2,models=MODEL_INFO,au_names=AU_NAMES,labels=LABELS)

@app.post('/analyze')
def analyze():
    mode = request.form.get('mode','detail')
    if mode not in ('baseline','compare','detail'):
        return jsonify(error='无效分析模式'),400
    upload = request.files.get('frame')
    if upload is None:
        return jsonify(error='缺少图像'),400
    data = upload.read(2*1024*1024+1)
    if len(data)>2*1024*1024:
        return jsonify(error='图像过大'),413
    image = cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_COLOR)
    if image is None or max(image.shape[:2])>1920:
        return jsonify(error='无效图像或尺寸过大'),400
    with lock:
        result = engines.analyze(image,mode)
    return jsonify(result)


def export_csv(path, rows):
    header = ['录像秒数','检测到人脸','模式','原模型预测'] + ['原模型_'+v for v in BASE_LABELS]
    header += ['EmotiEff预测'] + ['EmotiEff_'+v for v in EMOTI_LABELS]
    header += ['AU结果有效'] + [f'AU{k}_强度_0到5' for k in AU_INTENSITY]
    header += [f'AU{k}_出现' for k in AU_PRESENCE] + [f'AU{k}_出现得分' for k in AU_PRESENCE]
    header += ['总处理毫秒','原模型毫秒','EmotiEff毫秒','AU分析毫秒']
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f);writer.writerow(header)
        for row in rows:
            models=row.get('models') or {}
            baseline=models.get('baseline') or {}
            emoti=models.get('emotieff') or {}
            au=row.get('au') or {}
            writer.writerow([row.get('seconds'),row.get('face'),row.get('mode'),baseline.get('label','')]
                +baseline.get('scores',['']*7)+[emoti.get('label','')]+emoti.get('scores',['']*8)
                +[bool(au)]+[(au.get('intensity') or {}).get(str(k),'') for k in AU_INTENSITY]
                +[(au.get('presence') or {}).get(str(k),'') for k in AU_PRESENCE]
                +[(au.get('presence_scores') or {}).get(str(k),'') for k in AU_PRESENCE]
                +[row.get('total_ms',''),baseline.get('ms',''),emoti.get('ms',''),au.get('ms','')])

@app.errorhandler(413)
def too_large(error):
    return jsonify(error='请求超过 200 MB 上限，请缩短录像'),413

@app.post('/save')
def save():
    video=request.files.get('video')
    if video is None:
        return jsonify(error='缺少录像'),400
    try:
        rows=json.loads(request.form.get('metrics','[]'))
        validate_rows(rows)
    except (ValueError,TypeError):
        return jsonify(error='无效分析数据'),400
    folder=ROOT/'recordings'/datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    folder.mkdir(parents=True)
    video.save(folder/'video.webm')
    export_csv(folder/'predictions.csv',rows)
    (folder/'analysis.json').write_text(json.dumps({'models':MODEL_INFO,'samples':rows},ensure_ascii=False,indent=2),encoding='utf-8')
    (folder/'README.txt').write_text('video.webm 为无声原始录像；predictions.csv/analysis.json 为同帧模型预测与AU时间线。表情分数未经校准，不代表真实心理概率；AU强度为0–5的模型估计。不同AU检测头和强度头支持的AU集合不同，不能混为同一指标。无脸/关键点失败时AU为空。仅用于个人实验。\n',encoding='utf-8')
    return jsonify(path=str(folder),session=folder.name,samples=len(rows))

@app.get('/recordings/<session>/<filename>')
def recording(session,filename):
    if not re.fullmatch(r'[0-9-]+',session) or filename not in ('video.webm','predictions.csv','analysis.json'):
        abort(404)
    return send_from_directory(ROOT/'recordings'/session,filename)
