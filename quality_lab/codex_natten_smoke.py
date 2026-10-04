"""Exercise the actual NAF attention backend; no model weights required."""
import argparse
import json
import platform
from pathlib import Path
import torch
import natten

p = argparse.ArgumentParser()
p.add_argument('--out', required=True)
a = p.parse_args()
assert torch.cuda.is_available()
assert natten.HAS_LIBNATTEN
torch.manual_seed(42)
results = []
for dilation in (1, 2, 4):
    # NAF uses channels-last local attention with a 9x9 neighborhood.
    q, k, v = [torch.randn(1, 40, 40, 4, 32, device='cuda', dtype=torch.float16)
               for _ in range(3)]
    y = natten.na2d(q, k, v, kernel_size=(9, 9), dilation=(dilation, dilation),
                   stride=1, backend='cutlass-fna')
    torch.cuda.synchronize()
    assert y.shape == q.shape and torch.isfinite(y).all()
    # A constant value field must remain constant after softmax-weighted attention.
    c = natten.na2d(q, k, torch.ones_like(v), kernel_size=(9, 9),
                   dilation=(dilation, dilation), stride=1, backend='cutlass-fna')
    error = (c.float() - 1).abs().max().item()
    assert error < .01, error
    results.append({'dilation': dilation, 'shape': list(y.shape),
                    'constant_value_max_error': error})
report = {'python': platform.python_version(), 'torch': torch.__version__,
          'natten': natten.__version__, 'gpu': torch.cuda.get_device_name(),
          'backend': 'cutlass-fna', 'tests': results, 'passed': True,
          'scope': 'Attention runtime only; not model inference or quality acceptance'}
Path(a.out).write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
