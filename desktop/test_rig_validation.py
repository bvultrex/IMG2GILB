import unittest
import numpy as np
from validate_rig import validate


def fixture(weights=(1, 0, 0, 0), joints=(0, 1, 0, 0)):
    arrays = [np.zeros((3, 3), '<f4'), np.tile(joints, (3, 1)).astype('<u2'),
              np.tile(weights, (3, 1)).astype('<f4')]
    binary = b''
    views = []
    for a in arrays:
        views.append({'byteOffset': len(binary), 'byteLength': a.nbytes})
        binary += a.tobytes()
    doc = {'buffers': [{'byteLength': len(binary)}], 'bufferViews': views,
           'accessors': [{'bufferView': i, 'componentType': c, 'type': t, 'count': 3}
                         for i, c, t in [(0, 5126, 'VEC3'), (1, 5123, 'VEC4'), (2, 5126, 'VEC4')]],
           'nodes': [{'children': [1]}, {}, {'mesh': 0, 'skin': 0}],
           'skins': [{'joints': [0, 1]}],
           'meshes': [{'primitives': [{'attributes': {'POSITION': 0, 'JOINTS_0': 1, 'WEIGHTS_0': 2}}]}]}
    return doc, binary


class RigContract(unittest.TestCase):
    def test_valid_skin(self):
        self.assertEqual(validate(*fixture())['status'], 'passed')

    def test_unweighted_vertex_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unweighted'):
            validate(*fixture(weights=(0, 0, 0, 0)))

    def test_nonfinite_weight_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Invalid skin weights'):
            validate(*fixture(weights=(float('nan'), 0, 0, 0)))

    def test_invalid_joint_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Joint index'):
            validate(*fixture(joints=(9, 0, 0, 0)))

    def test_cycle_rejected(self):
        doc, binary = fixture()
        doc['nodes'][1]['children'] = [0]
        with self.assertRaisesRegex(ValueError, 'Cyclic'):
            validate(doc, binary)

    def test_unrigged_rejected(self):
        doc, binary = fixture()
        doc['skins'] = []
        with self.assertRaisesRegex(ValueError, 'No skeleton'):
            validate(doc, binary)


if __name__ == '__main__':
    unittest.main()
