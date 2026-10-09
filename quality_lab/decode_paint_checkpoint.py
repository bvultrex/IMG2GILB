"""Decode saved VAE input in a fresh process, one view at a time."""
import argparse
import json
import os
from pathlib import Path

os.environ['HF_HUB_OFFLINE'] = '1'
import torch
from diffusers import AutoencoderKL
from diffusers.image_processor import VaeImageProcessor

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
args = parser.parse_args()
z = torch.load(args.directory/'vae_decode_input.pt', map_location='cpu', weights_only=True)
assert z.ndim == 4 and z.shape[0] == 12, z.shape
vae = AutoencoderKL.from_pretrained(
    'D:/SF3D_QualityLab/models/tencent/Hunyuan3D-2.1/hunyuan3d-paintpbr-v2-1/vae',
    torch_dtype=torch.float16, local_files_only=True).eval().cuda()
vae.enable_tiling()
processor = VaeImageProcessor()
with torch.inference_mode():
    for index in range(len(z)):
        print('DECODE', index, flush=True)
        decoded = vae.decode(z[index:index+1].cuda(), return_dict=False)[0]
        image = processor.postprocess(decoded, output_type='pil')[0]
        image.save(args.directory/f'{"albedo" if index < 6 else "mr"}_{index % 6}.png')
        del decoded
        torch.cuda.empty_cache()
(args.directory/'decode_report.json').write_text(json.dumps({
    'status': 'passed', 'views': 6, 'native_resolution': list(image.size),
    'source': 'persisted VAE decode input; no resampling', 'decode_batch': 1}, indent=2))
