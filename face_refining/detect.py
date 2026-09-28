import argparse,json,sys,time
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--images',nargs='+',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
c=json.loads(Path(a.config).read_text());sys.path[:0]=[str(Path(__file__).resolve().parent),c['detector_source'],c['extra_deps']]
import cv2,torch
from anime_face_detector.detector import LandmarkDetector
from detection_policy import retry_crop,consistent_retry
torch.set_num_threads(4)
d=LandmarkDetector(c['models']['hrnetv2']['path'],face_detector_name='yolov3',face_detector_checkpoint_path=c['models']['yolov3']['path'],device='cpu')
result=[]
for path in a.images:
 im=cv2.imread(path)
 if im is None:raise ValueError('Cannot read input image: '+path)
 start=time.monotonic();faces=d(im);mode='full_frame';retry=None
 crop=retry_crop(faces,im.shape)
 if crop is not None:
  x,y,xx,yy=crop;candidates=d(im[y:yy,x:xx])
  for f in candidates:
   f['bbox'][:4]+=[x,y,x,y];f['keypoints'][:,:2]+=[x,y]
  accepted=consistent_retry(faces[0],candidates)
  retry={'crop':crop,'accepted':accepted,'original_bbox':faces[0]['bbox'].tolist()}
  if accepted:faces=candidates;mode='context_retry'
 result.append({'path':path,'seconds':time.monotonic()-start,'detection_mode':mode,'retry':retry,'faces':[{'bbox':f['bbox'].tolist(),'keypoints':f['keypoints'].tolist()} for f in faces]})
Path(a.output).write_text(json.dumps(result,indent=2))
