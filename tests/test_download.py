import base64
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from face_lab import download

class ModelDownloadTests(unittest.TestCase):
    def test_corrupt_model_is_repaired_and_valid_model_skipped(self):
        payload=b'model-fixture';entry={'path':'test.onnx','bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),'url':'https://example.invalid/model'}
        with tempfile.TemporaryDirectory() as tmp,patch.object(download,'MANIFEST',{'files':[entry]}):
            p=Path(tmp)/'test.onnx';p.write_bytes(b'corrupt')
            with patch.object(download.urllib.request,'urlopen',return_value=io.BytesIO(payload)) as request:
                # Supply the response headers expected by fetch().
                request.return_value.headers={'Content-Length':str(len(payload))}
                download.download_models(tmp)
            self.assertEqual(p.read_bytes(),payload)
            with patch.object(download,'fetch') as fetch:
                download.download_models(tmp);fetch.assert_not_called()

    def test_wrong_model_hash_is_rejected(self):
        entry={'path':'test.onnx','bytes':3,'sha256':'0'*64,'url':'https://example.invalid/model'}
        with tempfile.TemporaryDirectory() as tmp,patch.object(download,'MANIFEST',{'files':[entry]}):
            def fake_fetch(url,path):Path(path).write_bytes(b'bad')
            with patch.object(download,'fetch',side_effect=fake_fetch):
                with self.assertRaises(RuntimeError):download.download_models(tmp)
            self.assertFalse((Path(tmp)/'test.onnx').exists())

    def test_verified_archive_extracts_only_manifest_member(self):
        payload=b'au-model';member='content/model.onnx'
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as z:z.writestr(member,payload);z.writestr('unused.onnx',b'unused')
        archive=buf.getvalue()
        manifest={'files':[{'path':'au/model.onnx','bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),'archive_member':member}],
                  'libreface_package':{'url':'https://example.invalid/package','filename':'package.zip','sha512_base64':base64.b64encode(hashlib.sha512(archive).digest()).decode()}}
        with tempfile.TemporaryDirectory() as tmp,patch.object(download,'MANIFEST',manifest):
            def fake_fetch(url,path):Path(path).parent.mkdir(parents=True);Path(path).write_bytes(archive)
            with patch.object(download,'fetch',side_effect=fake_fetch):download.download_models(tmp)
            self.assertEqual((Path(tmp)/'au/model.onnx').read_bytes(),payload)
            self.assertFalse((Path(tmp)/'unused.onnx').exists())

if __name__=='__main__':unittest.main()
