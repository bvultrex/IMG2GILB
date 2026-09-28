"""Process-local dependency paths; leaves ComfyUI and rig environments untouched."""
import os,sys
from pathlib import Path
runtime=Path(r'C:\Users\Shadow\Documents\ComfyUI\IMG2GILB-trellis-runtime')
sys.path[:0]=[str(runtime/'deps'),str(runtime/'source')]
os.environ.update(ATTN_BACKEND='sdpa',SPARSE_ATTN_BACKEND='sdpa',CC=str(runtime/'deps/triton/runtime/tcc/tcc.exe'),CUDA_PATH=str(runtime/'deps/triton/backends/nvidia'),HF_HOME=str(runtime/'hf'),TRITON_CACHE_DIR=str(runtime/'triton_cache'))
