import trellis_bootstrap
import torch
from trellis2.modules.sparse import VarLenTensor,sparse_scaled_dot_product_attention
torch.manual_seed(1)
def reference(q,k,v):
 q,k,v=[x.transpose(0,1) for x in (q,k,v)]
 return ((q@k.transpose(-1,-2)/q.shape[-1]**.5).softmax(-1)@v).transpose(0,1)
for device in ['cpu','cuda']:
 qs=[torch.randn(n,2,8,device=device) for n in [3,5]];ks=[torch.randn(n,2,8,device=device) for n in [4,6]];vs=[torch.randn_like(k) for k in ks]
 q,k,v=[VarLenTensor.from_tensor_list(x) for x in [qs,ks,vs]]
 got=sparse_scaled_dot_product_attention(q,k,v).feats;expected=torch.cat([reference(*x) for x in zip(qs,ks,vs)])
 torch.testing.assert_close(got,expected,atol=1e-5,rtol=1e-5)
 qkv=VarLenTensor.from_tensor_list([torch.stack([a,a,a],1) for a in qs]);got=sparse_scaled_dot_product_attention(qkv).feats
 torch.testing.assert_close(got,torch.cat([reference(a,a,a) for a in qs]),atol=1e-5,rtol=1e-5)
print('Ragged self/cross SDPA matches explicit attention on CPU and CUDA')
