"""End-to-end check against running server, using a sample-only Y4M camera."""
import csv
import json
from pathlib import Path
import shutil
import sys
import os
import tempfile
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH'),headless=True,args=[
        '--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream',
        '--use-file-for-fake-video-capture='+str(Path(sys.argv[1]).resolve())])
    context=browser.new_context(permissions=['camera'],viewport={'width':1440,'height':1100})
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    base_url=os.environ.get('FACE_LAB_URL','http://127.0.0.1:8766')
    page.goto(base_url)
    page.get_by_role('button',name='开启摄像头',exact=True).click()
    page.wait_for_function("document.getElementById('av12').textContent !== '—'")
    assert page.locator('#baseTime').inner_text()
    assert page.locator('#emotiTime').inner_text()
    assert page.locator('#auStatus').inner_text().startswith('强度为模型估计')
    page.wait_for_timeout(800)
    if os.environ.get('FACE_LAB_SCREENSHOT'):
        page.screenshot(path=os.environ['FACE_LAB_SCREENSHOT'],full_page=True)
    page.locator('#trendAU').select_option('4')
    page.get_by_role('button',name='开始录制',exact=True).click()
    assert page.locator('#mode').is_disabled()
    page.wait_for_timeout(1700)
    with page.expect_response(lambda r:'/save' in r.url) as response:
        page.get_by_role('button',name='结束并保存',exact=True).click()
    saved=response.value.json()
    page.wait_for_function("document.getElementById('saved').textContent.includes('完整 JSON')")
    folder=Path(saved['path'])
    try:
        assert saved['samples']>=2,saved
        rows=list(csv.DictReader((folder/'predictions.csv').open(encoding='utf-8-sig')))
        assert len(rows)==saved['samples']
        assert all(row['AU结果有效']=='True' for row in rows)
        assert all(row['原模型预测'] and row['EmotiEff预测'] for row in rows)
        assert all(float(row['录像秒数'])>=0 for row in rows)
        assert (folder/'video.webm').stat().st_size>1000
        complete=json.loads((folder/'analysis.json').read_text())
        assert all('au' in row and len(row['models'])==2 for row in complete['samples'])
        for name in ['video.webm','predictions.csv','analysis.json']:
            assert context.request.get(base_url+'/recordings/'+folder.name+'/'+name).status==200
        page.locator('#mode').select_option('baseline')
        page.wait_for_function("document.getElementById('baseTime').textContent.includes('ms') && document.getElementById('emotiLabel').textContent === '未启用'")
        assert page.locator('#av12').inner_text()=='—'
        page.locator('#mode').select_option('compare')
        page.wait_for_function("document.getElementById('emotiTime').textContent.includes('ms')")
        assert page.locator('#av12').inner_text()=='—'
        page.locator('#mode').select_option('detail')
        page.wait_for_function("document.getElementById('av12').textContent !== '—'")
        page.get_by_role('button',name='关闭摄像头',exact=True).click()
        assert page.locator('#baseLabel').inner_text()=='摄像头已关闭'
        assert page.locator('#av12').inner_text()=='—'
        assert page.evaluate("document.getElementById('video').srcObject === null")
        assert not errors,errors
        print('PASS: real face predictions/AUs, chart, all modes, record/save/playback, CSV/JSON, camera stop. Samples:',saved['samples'])
        browser.close()
    finally:
        assert folder.parent.name == 'recordings' and folder.name == saved['session']
        shutil.rmtree(folder)
