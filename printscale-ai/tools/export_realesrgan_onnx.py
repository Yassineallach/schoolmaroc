import sys, json, torch, torch.nn as nn, torch.nn.functional as F, numpy as np, onnx, onnxruntime as ort
mdir, out = sys.argv[1], sys.argv[2]
class SRVGG(nn.Module):
    def __init__(s, nf=64, nc=32, up=4):
        super().__init__(); s.up=up; s.body=nn.ModuleList([nn.Conv2d(3,nf,3,1,1), nn.PReLU(nf)])
        for _ in range(nc): s.body += [nn.Conv2d(nf,nf,3,1,1), nn.PReLU(nf)]
        s.body.append(nn.Conv2d(nf,3*up*up,3,1,1)); s.ups=nn.PixelShuffle(up)
    def forward(s,x):
        o=x
        for m in s.body: o=m(o)
        return torch.clamp(s.ups(o)+F.interpolate(x,scale_factor=s.up,mode='nearest'),0,1)
res={}
for name in ['realesr-general-x4v3','realesr-general-wdn-x4v3']:
    m=SRVGG(); sd=torch.load(f'{mdir}/{name}.pth',map_location='cpu'); m.load_state_dict(sd['params'] if 'params' in sd else sd['params_ema']); m.eval()
    p=f'{out}/{name}.onnx'
    torch.onnx.export(m,torch.rand(1,3,64,64),p,input_names=['input'],output_names=['output'],opset_version=17,
        dynamic_axes={'input':{2:'h',3:'w'},'output':{2:'H',3:'W'}},dynamo=False, do_constant_folding=True)
    x=torch.rand(1,3,37,53)
    with torch.no_grad(): ref=m(x).numpy()
    y=ort.InferenceSession(p).run(None,{'input':x.numpy()})[0]
    print(name, y.shape, 'maxdiff', float(np.abs(y-ref).max()))
    res[name]=(p,m)
# blend map: offsets of each initializer's raw bytes, identical across both files
a=open(res['realesr-general-x4v3'][0],'rb').read(); b=open(res['realesr-general-wdn-x4v3'][0],'rb').read()
assert len(a)==len(b)
ma=onnx.load(res['realesr-general-x4v3'][0]); ranges=[]
for init in ma.graph.initializer:
    if init.data_type!=1: continue
    raw=init.raw_data; off=a.find(raw); assert off>=0 and a.find(raw,off+1)<0, init.name
    ranges.append([off,len(raw)])
# verify blending bytes == blending torch weights
dn=0.4
fa=np.frombuffer(a,dtype=np.uint8).copy(); out_b=bytearray(a)
for off,ln in ranges:
    va=np.frombuffer(a,dtype='<f4',count=ln//4,offset=off); vb=np.frombuffer(b,dtype='<f4',count=ln//4,offset=off)
    out_b[off:off+ln]=(dn*va+(1-dn)*vb).astype('<f4').tobytes()
mt=SRVGG(); sa=res['realesr-general-x4v3'][1].state_dict(); sb=res['realesr-general-wdn-x4v3'][1].state_dict()
mt.load_state_dict({k:dn*sa[k]+(1-dn)*sb[k] for k in sa}); mt.eval()
x=torch.rand(1,3,40,40)
with torch.no_grad(): ref=mt(x).numpy()
y=ort.InferenceSession(bytes(out_b)).run(None,{'input':x.numpy()})[0]
print('blend maxdiff',float(np.abs(y-ref).max()), 'ranges',len(ranges), 'bytes', len(a))
json.dump({'ranges':ranges,'size':len(a)},open(f'{out}/blend_map.json','w'))
