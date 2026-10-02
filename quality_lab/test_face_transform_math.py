import unittest
import cv2
import numpy as np
from face_transform_math import ecc_to_forward, face_feature_indices, blend_valid_face_interior, gate_post_warp

class ECCDirectionTest(unittest.TestCase):
 def test_post_warp_rejection_changes_projection_weights(self):
  image=np.zeros((8,8,4),np.uint8)
  weights=np.ones((8,8))
  result=(image,None,.9,{'project_face':True,'accepted':True,'weight_roi':[1,1,7,7]},weights)
  def fallback(mask,roi,**kwargs):
   self.assertFalse(kwargs['project_face'])
   self.assertEqual(roi,(1,1,7,7))
   return np.zeros((8,8))
  for quality in ({'ok':False},{}):
   gated=gate_post_warp(result,quality,fallback)
   self.assertFalse(gated[3]['project_face'])
   self.assertEqual(gated[4].sum(),0)
   self.assertIs(gated[0],image)
  passed=gate_post_warp(result,{'ok':True},fallback)
  self.assertTrue(passed[3]['project_face'])
  self.assertIs(passed[4],weights)
 def test_near_opaque_interpolation_does_not_leave_old_features(self):
  source=np.zeros((64,64,4),np.uint8);source[:,:,3]=254
  candidate=source.copy();candidate[:,:,:3]=220;candidate[:,:,3]=253
  source[0,:,3]=0;candidate[0,:,3]=0
  result=blend_valid_face_interior(source,candidate)
  np.testing.assert_array_equal(result[:,:,3],source[:,:,3])
  np.testing.assert_array_equal(result[32,32,:3],[220,220,220])
  np.testing.assert_array_equal(result[0,:,:3],source[0,:,:3])
 def test_documented_feature_schema_excludes_contour(self):
  ids=face_feature_indices(28)
  self.assertEqual(ids,list(range(11,28)))
  self.assertTrue({23,24,25,26,27}.issubset(ids))
  self.assertTrue(set(ids).isdisjoint(range(11)))
  self.assertEqual(face_feature_indices(5),list(range(5)))
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
