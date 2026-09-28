"""Contract and rejection tests using actual detector outputs plus corrupt inputs."""
import copy,json,unittest
from pathlib import Path
import numpy as np
from PIL import Image
from core import checked_face,warp_face,blend_face,Rejected,coloured_fringe
P=Path(__file__).parent;R=P.parent
class FaceTests(unittest.TestCase):
 def test_protected_eye_white_does_not_mix_dark_target(self):
  source=np.full((128,128,4),255,np.uint8);target=np.zeros_like(source);target[:,:,3]=255
  mask=np.zeros((128,128),np.uint8);mask[20:108,20:108]=1
  alpha=mask.astype(np.float32)
  result=blend_face(source,target,mask,alpha,'multiband',[[[50,50],[78,50],[78,70],[50,70]]])
  self.assertGreater(result[60,64].min(),.99)
 def test_fringe_palette_does_not_classify_dark_brows(self):
  image=np.full((160,160,4),255,np.uint8);image[:,:,:3]=[220,170,140]
  image[12:45,40:110,:3]=[45,30,25]
  image[60:65,55:105,:3]=[65,35,20]
  centers=np.array([[55,80],[105,80],[80,115]],float)
  landmarks=np.zeros((28,3));landmarks[5:11,1]=70
  result=coloured_fringe(image,centers,landmarks,np.array([220,170,140]))
  self.assertFalse(result.any())
 def test_fringe_palette_matches_coloured_hair_not_skin(self):
  image=np.full((160,160,4),255,np.uint8);image[:,:,:3]=[220,170,140]
  image[10:50,40:120,:3]=[200,85,15]
  image[60:65,60:65,:3]=[200,85,15]
  centers=np.array([[55,80],[105,80],[80,115]],float)
  landmarks=np.zeros((28,3));landmarks[5:11,1]=70
  result=coloured_fringe(image,centers,landmarks,np.array([220,170,140]))
  self.assertTrue(result[62,62]);self.assertFalse(result[90,90])
 @classmethod
 def setUpClass(cls):
  cls.lm=json.loads((R/'anime_test/face_auto/landmarks.json').read_text())
  cls.good=json.loads((P/'tests/detections_padded.json').read_text())
  cls.faces=cls.lm['source']['faces'];cls.detect=json.loads((P/'tests/detections.json').read_text())
 def test_valid_face(self):checked_face(self.faces,(1280,1280,4))
 def test_blank_real_detection(self):
  self.assertEqual(len(self.detect[0]['faces']),0)
  with self.assertRaises(Rejected):checked_face(self.detect[0]['faces'],(512,512,4))
 def test_multiple_real_detection(self):
  self.assertGreater(len(self.detect[1]['faces']),1)
  with self.assertRaises(Rejected):checked_face(self.detect[1]['faces'],(400,800,4))
 def test_nan(self):
  f=copy.deepcopy(self.faces);f[0]['keypoints'][12][0]=float('nan')
  with self.assertRaises(Rejected):checked_face(f,(1280,1280,4))
 def test_low_score(self):
  f=copy.deepcopy(self.faces);f[0]['bbox'][4]=.4
  with self.assertRaises(Rejected):checked_face(f,(1280,1280,4))
 def test_low_eye_confidence(self):
  f=copy.deepcopy(self.faces)
  for i in range(11,17):f[0]['keypoints'][i][2]=.1
  with self.assertRaises(Rejected):checked_face(f,(1280,1280,4))
 def test_clipped(self):
  f=copy.deepcopy(self.faces);f[0]['keypoints'][0][0]=-1
  with self.assertRaises(Rejected):checked_face(f,(1280,1280,4))
 def test_impossible_mouth(self):
  f=copy.deepcopy(self.faces)
  for i in range(24,28):f[0]['keypoints'][i][1]=10
  with self.assertRaises(Rejected):checked_face(f,(1280,1280,4))
 def test_tiny_face(self):
  f=copy.deepcopy(self.faces)
  for point in f[0]['keypoints']:point[0]*=.1;point[1]*=.1
  with self.assertRaises(Rejected):checked_face(f,(1280,1280,4))
 def test_independent_head_alignment(self):
  a=np.array(Image.open(P/'tests/independent_open_target.png').convert('RGBA'));b=np.array(Image.open(P/'tests/independent_padded_target.png').convert('RGBA'))
  w,m,alpha,rep=warp_face(a,b,self.good[0]['faces'],self.good[1]['faces'])
  self.assertTrue(.7<rep['eye_scale']<.9);self.assertLess(np.linalg.norm(rep['mouth_delta']),5)
  rgb=blend_face(w,b,m,alpha,'multiband');self.assertTrue(np.isfinite(rgb).all());self.assertTrue((rgb>=0).all() and (rgb<=1).all())
 def test_uncertain_independent_face_rejected(self):
  with self.assertRaises(Rejected):checked_face(self.detect[2]['faces'],(460,512,4))
 def test_transparent_source_rejected(self):
  a=np.array(Image.open(R/'anime_test/front.png').convert('RGBA'));a[:,:,3]=0
  b=np.array(Image.open(R/'anime_test/face_auto/baseline.png').convert('RGBA'))
  with self.assertRaises(Rejected):warp_face(a,b,self.faces,self.lm['baseline']['faces'])
if __name__=='__main__':unittest.main(verbosity=2)
