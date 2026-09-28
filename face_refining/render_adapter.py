"""Conservative reference projection experiment; never overwrites Paint baseline."""
import sys,json,time,hashlib
from pathlib import Path
import numpy as np,cv2,torch,trimesh
from scipy.spatial import Delaunay
from PIL import Image
r=Path(__file__).parent
import os
sys.path.insert(0,os.environ['IMG2GILB_HUNYUAN_SOURCE'])
from hy3dgen.texgen.differentiable_renderer.mesh_render import MeshRender
from hy3dgen.texgen.differentiable_renderer.mesh_render import transform_pos
class ProjectionRender(MeshRender):
 # Upstream _render retains a stale glctx argument although raster_rasterize no longer takes it.
 def _render(self,mvp,pos,pos_idx,uv,uv_idx,tex,resolution,max_mip_level,keep_alpha,filter_mode):
  clip=transform_pos(mvp,pos)
  rast,_=self.raster_rasterize(clip,pos_idx,resolution=resolution)
  coords,_=self.raster_interpolate(uv[None,...],rast,uv_idx)
  color=torch.nn.functional.grid_sample(tex.permute(2,0,1)[None,...],coords*2-1,mode='bilinear',padding_mode='border',align_corners=True).permute(0,2,3,1)
  mask=rast[...,-1:].clamp(0,1)
  return torch.cat([color*mask,mask],dim=-1)[0]


