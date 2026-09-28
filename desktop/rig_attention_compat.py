"""Local Windows inference adapter; explicit backend, no model-weight changes."""
import os
import torch.nn.functional as F

BACKEND = os.environ.get("IMG2GILB_ATTENTION_BACKEND", "sdpa" if os.name == "nt" else "flash_attention_2")
if BACKEND not in ("sdpa", "flash_attention_2"):
    raise ValueError("Unsupported attention backend: " + BACKEND)

def flash_attn_func(q, k, v):
    if BACKEND == "flash_attention_2":
        from flash_attn.flash_attn_interface import flash_attn_func as flash
        return flash(q, k, v), None
    # Existing callers use B,L,H,D and expect a tuple from the FA3 convention.
    q, k, v = [x.transpose(1, 2) for x in (q, k, v)]
    if q.shape[1] != k.shape[1]:
        if q.shape[1] % k.shape[1]:
            raise ValueError("Query heads must be divisible by key heads")
        factor = q.shape[1] // k.shape[1]
        k = k.repeat_interleave(factor, dim=1)
        v = v.repeat_interleave(factor, dim=1)
    return F.scaled_dot_product_attention(q, k, v, dropout_p=0.0).transpose(1, 2), None
