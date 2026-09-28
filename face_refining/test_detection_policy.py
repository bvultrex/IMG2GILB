import copy
import unittest
import numpy as np
from detection_policy import retry_crop, consistent_retry

def face(score=.2):
    points=np.tile([100.,100.,.9],(28,1))
    points[11:17,:2]=[80,90];points[17:23,:2]=[120,90];points[24:28,:2]=[100,120]
    return {'bbox':[50,50,150,150,score],'keypoints':points.tolist()}

class RetryPolicy(unittest.TestCase):
    def test_single_precise_weak_detection_gets_crop(self):
        self.assertEqual(retry_crop([face()],(1000,1000,3)),[0,0,200,200])
    def test_already_confident_and_multiple_faces_do_not_retry(self):
        self.assertIsNone(retry_crop([face(.99)],(1000,1000,3)))
        self.assertIsNone(retry_crop([face(),face()],(1000,1000,3)))
        self.assertIsNone(retry_crop([],(1000,1000,3)))
    def test_weak_features_do_not_get_promoted(self):
        f=face();f['keypoints'][24][2]=.1
        self.assertIsNone(retry_crop([f],(1000,1000,3)))
    def test_consistent_confident_retry_accepted(self):
        self.assertTrue(consistent_retry(face(),[face(.99)]))
    def test_shifted_or_multiple_candidates_rejected(self):
        f=face(.99);p=np.array(f['keypoints']);p[:,:2]+=20;f['keypoints']=p.tolist()
        self.assertFalse(consistent_retry(face(),[f]))
        self.assertFalse(consistent_retry(face(),[face(.99),face(.99)]))
    def test_nonfinite_rejected(self):
        f=face();f['keypoints'][0][0]=float('nan')
        self.assertIsNone(retry_crop([f],(1000,1000,3)))
        self.assertFalse(consistent_retry(f,[face(.99)]))

if __name__=='__main__':unittest.main(verbosity=2)
