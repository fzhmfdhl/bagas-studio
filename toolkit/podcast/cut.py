import numpy as np, glob, json, os
from PIL import Image
from scipy import ndimage as ndi
os.makedirs('cells',exist_ok=True)
def keyg(a):
    a=a.astype(np.float32); r,g,b=a[...,0],a[...,1],a[...,2]
    d=g-np.maximum(r,b)
    al=np.clip((70-d)/40,0,1)
    # despill
    m=np.maximum(r,b); g2=np.where(g>m,m+(g-m)*0.15,g)
    out=np.dstack([r,g2,b,al*255]).clip(0,255).astype(np.uint8)
    fg=al>0.5
    lab,n=ndi.label(fg)
    if n>1:
        sz=ndi.sum(fg,lab,range(1,n+1)); keep=np.zeros(n+1,bool)
        keep[1:]=sz>max(800,sz.max()*0.02)
        out[...,3]=np.where(keep[lab],out[...,3],0)
    return out
info={}
for n in ['Nabila','Herman','Rusdi','Laut','Bagas','Baby','Nadine','Sonya','SonyaB']:
    fs=sorted(glob.glob(f'sh/{n}_Sheet/*.jpg') or glob.glob(f'sh/{n}/*.jpg'))
    for si,f in enumerate(fs):
        a=np.asarray(Image.open(f).convert('RGB'))
        W=a.shape[1]
        for c in range(3):
            x0=int(c*W/3); x1=int((c+1)*W/3)
            o=keyg(a[:,x0:x1]); al=o[...,3]>128
            ys,xs=np.where(al)
            bot=ys.max(); top=ys.min()
            # jangkar: pusat x dari 20% baris paling bawah (kaki kursi + sepatu)
            lo=al[int(bot-(bot-top)*0.2):bot+1]; bx=np.where(lo.any(0))[0]
            k=f'{n}_{si}{c}'
            Image.fromarray(o).save(f'cells/{k}.png')
            info[k]=dict(top=int(top),bot=int(bot),ax=float((bx.min()+bx.max())/2),w=o.shape[1],h=o.shape[0],l=int(xs.min()),r=int(xs.max()))
json.dump(info,open('cells.json','w'),indent=0)
for n in ['Nabila','Herman']:
    print(n,[(k[-2:],v['top'],v['bot'],round(v['ax'])) for k,v in info.items() if k.startswith(n)])
