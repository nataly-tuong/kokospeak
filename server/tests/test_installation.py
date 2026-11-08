"""Offline installer/path/launcher checks: never download or install anything."""
from pathlib import Path
import hashlib
import importlib.util
import io
import json
import os
import socket
import shutil
import subprocess
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'server'))
from src import runtime


def load_file(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

setup=load_file('kokospeak_setup',ROOT/'scripts'/'setup.py')
launcher=load_file('kokospeak_launcher',ROOT/'launch.py')

class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.root_patch=patch.object(setup,'ROOT',self.root);self.root_patch.start()
        self.runtime_patch=patch.object(setup,'RUNTIME',self.root/'.runtime');self.runtime_patch.start()
        self.addCleanup(self.temp.cleanup);self.addCleanup(self.root_patch.stop);self.addCleanup(self.runtime_patch.stop)

    def test_native_node_targets(self):
        self.assertEqual(setup.node_target('darwin','arm64'),('darwin','arm64'))
        self.assertEqual(setup.node_target('win32','AMD64'),('win','x64'))
        self.assertEqual(setup.node_target('linux','aarch64'),('linux','arm64'))
        with self.assertRaises(RuntimeError):setup.node_target('linux','riscv64')

    def test_zip_rejects_traversal_and_symlinks(self):
        for name,symlink in (('../../escape',False),('link',True)):
            file=self.root/'node.zip'
            with zipfile.ZipFile(file,'w') as archive:
                item=zipfile.ZipInfo(name)
                if symlink:item.external_attr=(stat.S_IFLNK|0o777)<<16
                archive.writestr(item,'outside')
            with self.assertRaises(ValueError):setup.safe_extract(file,self.root/'unpacked')
        self.assertFalse((self.root.parent/'escape').exists())

    def test_frontend_manifest_skips_build_and_detects_changes(self):
        client=self.root/'client';(client/'src').mkdir(parents=True);(client/'public').mkdir()
        (client/'package.json').write_text('{}')
        source=client/'src'/'App.tsx';source.write_text('export default 1')
        dist=client/'dist';dist.mkdir();(dist/'index.html').write_text('<html></html>')
        setup.write_json(dist/'.kokospeak-build.json',{'sourceFingerprint':setup.frontend_fingerprint()})
        with patch.object(setup,'ensure_node',side_effect=RuntimeError('needs rebuild')) as node:
            setup.install_frontend();node.assert_not_called()
            source.write_text('export default 2')
            with self.assertRaisesRegex(RuntimeError,'needs rebuild'):setup.install_frontend()

    def test_download_checksum(self):
        payload=b'node archive test'
        def response(*args,**kwargs):
            result=io.BytesIO(payload);result.headers={'Content-Length':str(len(payload))};return result
        target=self.root/'download.zip'
        with patch.object(setup.urllib.request,'urlopen',side_effect=response),patch.object(setup.time,'sleep'):
            setup.download('https://example.test/node',target,hashlib.sha256(payload).hexdigest())
            self.assertEqual(target.read_bytes(),payload)
            target.unlink()
            with self.assertRaises(OSError):setup.download('https://example.test/node',target,'0'*64)
            self.assertFalse(target.exists());self.assertFalse(target.with_name('download.zip.part').exists())

    @unittest.skipUnless(shutil.which('bash'),'bash unavailable')
    def test_shell_bootstrap_preserves_paths_and_selects_python312(self):
        project=self.root/'project with spaces';project.mkdir()
        shutil.copyfile(ROOT/'install.sh',project/'install.sh')
        uv=project/'.runtime'/'uv'/'uv';uv.parent.mkdir(parents=True)
        capture=self.root/'arguments.txt'
        uv.write_text('#!/bin/sh\nif [ "${VIRTUAL_ENV+x}" = x ]; then exit 97; fi\nprintf "%s\\n" "$@" > "$KOKOSPEAK_TEST_CAPTURE"\n')
        uv.chmod(0o755)
        environment=os.environ.copy();environment['VIRTUAL_ENV']='/old/environment';environment['KOKOSPEAK_TEST_CAPTURE']=str(capture)
        subprocess.run(['bash',str(project/'install.sh'),'--no-launch'],env=environment,check=True)
        arguments=capture.read_text().splitlines()
        self.assertEqual(arguments,['run','--no-project','--no-config','--python','3.12',str(project/'scripts'/'setup.py'),'--uv',str(uv),'--no-launch'])

    def test_private_python_is_reused(self):
        python=setup.RUNTIME/'python312'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
        python.parent.mkdir(parents=True);python.touch()
        server=self.root/'server';server.mkdir();(server/'requirements.txt').write_text('kokoro==0.9.4\n')
        with patch.object(setup.subprocess,'check_output',return_value='3.12\n'),patch.object(setup,'run') as run:
            _,fingerprint=setup.install_python('uv',False,False,{})
            self.assertEqual(run.call_count,2)
            run.reset_mock()
            setup.install_python('uv',False,False,{'pythonFingerprint':fingerprint})
            run.assert_not_called()

class RuntimeTests(unittest.TestCase):
    def tearDown(self):runtime.ffmpeg_executable.cache_clear()

    def test_writable_generated_directory(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'KOKOSPEAK_DATA_DIR':folder}):
            self.assertEqual(runtime.generated_dir(),Path(folder).resolve()/'generated')
        with patch.dict(os.environ,{},clear=True),patch.object(runtime.sys,'frozen',True,create=True),patch.object(runtime,'user_data_dir',return_value=Path('/user/data')):
            self.assertEqual(runtime.generated_dir(),Path('/user/data/generated'))

    def test_frozen_frontend_path(self):
        with patch.object(runtime.sys,'frozen',True,create=True),patch.object(runtime.sys,'_MEIPASS','/bundle',create=True):
            self.assertEqual(runtime.client_dist(),Path('/bundle/client/dist'))

    def test_ffmpeg_package_fallback(self):
        runtime.ffmpeg_executable.cache_clear()
        fake=type('FFmpeg',(),{'get_ffmpeg_exe':staticmethod(lambda:'/private/ffmpeg')})
        with patch.dict(os.environ,{},clear=True),patch.object(runtime.shutil,'which',return_value=None),patch.dict(sys.modules,{'imageio_ffmpeg':fake}):
            self.assertEqual(runtime.ffmpeg_executable(),'/private/ffmpeg')

class LauncherTests(unittest.TestCase):
    def test_port_conflict_falls_back_to_free_loopback_port(self):
        first=launcher.bind_local_socket(0)
        try:
            port=first.getsockname()[1]
            second=launcher.bind_local_socket(port)
            try:
                self.assertNotEqual(port,second.getsockname()[1])
                self.assertEqual(second.getsockname()[0],'127.0.0.1')
            finally:second.close()
        finally:first.close()

    def test_reuses_only_a_verified_instance(self):
        with tempfile.TemporaryDirectory() as folder:
            record=Path(folder)/'launcher.json'
            record.write_text(json.dumps({'port':8000,'token':'test','pid':123}))
            with patch.object(launcher,'health',return_value={'appId':'kokospeak'}):self.assertEqual(launcher.read_instance(record)['port'],8000)
            with patch.object(launcher,'health',return_value={'appId':'other'}):self.assertIsNone(launcher.read_instance(record))

    def test_session_capability_is_in_fragment(self):
        url=launcher.browser_url(8000,'test-token')
        self.assertEqual(url,'http://127.0.0.1:8000/#session=test-token')

if __name__=='__main__':unittest.main()
