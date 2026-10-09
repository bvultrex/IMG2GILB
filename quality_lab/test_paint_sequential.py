import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from run_paint_sequential import run_child, valid_checkpoint

class SequentialTests(unittest.TestCase):
    def test_corrupt_or_wrong_resolution_checkpoint_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'vae_decode_input.pt').write_bytes(b'checkpoint')
            report={'status':'sampling_complete_decode_pending','views':6,'resolution':1024,
                    'checkpoint_sha256':hashlib.sha256(b'checkpoint').hexdigest()}
            (root/'generation_checkpoint_report.json').write_text(json.dumps(report))
            valid_checkpoint(root,1024)
            with self.assertRaises(ValueError):valid_checkpoint(root,768)
            (root/'vae_decode_input.pt').write_bytes(b'truncated')
            with self.assertRaises(ValueError):valid_checkpoint(root,1024)

    def test_real_protected_children_complete_and_propagate_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            log=Path(directory)/'child.log'
            run_child([sys.executable,'-c',"print('child completed')"],log)
            self.assertIn('child completed',log.read_text())
            with self.assertRaises(RuntimeError):
                run_child([sys.executable,'-c','raise SystemExit(7)'],log)

if __name__=='__main__':unittest.main()
