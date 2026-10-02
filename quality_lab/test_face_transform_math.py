import unittest
import cv2
import numpy as np
from face_transform_math import ecc_to_forward

class ECCDirectionTest(unittest.TestCase):
 def test_known_translation_roundtrip(self):
  rng=np.random.default_rng(42)
  template=cv2.GaussianBlur(rng.random((160,160),dtype=np.float32),(0,0),3)
  shift=np.array([[1,0,4],[0,1,-6]],dtype=np.float32)
  source=cv2.warpAffine(template,shift,(160,160),borderMode=cv2.BORDER_REFLECT)
  mask=np.zeros((160,160),np.uint8);mask[20:-20,20:-20]=255
  _,sampling=cv2.findTransformECC(template,source,np.eye(2,3,dtype=np.float32),cv2.MOTION_TRANSLATION,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,150,1e-6),inputMask=mask,gaussFiltSize=5)
  delta=ecc_to_forward(sampling)
  np.testing.assert_allclose(delta[:,2],[-4,6],atol=.3)
  fixed=cv2.warpAffine(source,delta,(160,160))
  wrong=cv2.warpAffine(source,sampling,(160,160))
  crop=np.s_[24:-24,24:-24]
  fixed_error=np.mean((fixed[crop]-template[crop])**2)
  wrong_error=np.mean((wrong[crop]-template[crop])**2)
  self.assertLess(fixed_error,wrong_error*.05)

if __name__=='__main__':unittest.main()
