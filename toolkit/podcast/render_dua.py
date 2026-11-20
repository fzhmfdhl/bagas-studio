import sys, json, numpy as np, subprocess
from PIL import Image, ImageFilter, ImageDraw
from multiprocessing import Pool
CW,CH=3840,2160; OW,OH=1920,1080; FPS=24
TL=json.load(open('ep3/tl.json')); ENVS=TL['envs']; DUR=TL['total']; EV=TL['ev']
INFO=json.load(open('cells.json'))
# ---- latar
e=Image.open('env2.jpg').convert('RGB'); s=CH/e.height
e=e.resize((round(e.width*s),CH),Image.LANCZOS); ox=(e.width-CW)//2
BG=e.crop((ox,0,ox+CW,CH)).convert('RGBA')
# ---- tokoh: (nama, x jangkar, y lantai, tinggi target, idle closed/open/blink, mulut di sel)
CH_={'H':dict(n='Nadine',x=1300,y=1740,ht=972,idle=('00','01','02'),mouth=(262,178),key='D'),
     'N':dict(n='SonyaB',x=2560,y=1740,ht=936,idle=('00','01','02'),mouth=(240,218),sg=-1,flip=True,key='S')}
NORM=json.load(open('norm.json'))
BASE_S=936/652*393          # skala Nabila sebagai acuan, dihitung dari lebar kursi
TWEAK={'Sonya':1.0002}
for k,c in CH_.items():
    c['s']=BASE_S/NORM[c['n']]['chairw']*TWEAK.get(c['n'],1.0)
cache={}
def sprite(k,cell):
    key=(k,cell)
    if key not in cache:
        c=CH_[k]; i=INFO[f"{c['n']}_{cell}"]; im=Image.open(f"cells/{c['n']}_{cell}.png")
        s=c['s']; im=im.resize((round(im.width*s),round(im.height*s)),Image.NEAREST)
        a=np.asarray(im).astype(np.float32); a[...,:3]*=np.array([0.90,0.86,0.76]); im=Image.fromarray(a.clip(0,255).astype(np.uint8))
        ax=i['ax']
        if c.get('flip'): im=im.transpose(Image.FLIP_LEFT_RIGHT); ax=i['w']-ax
        cache[key]=(im,round(c['x']-ax*s),round(c['y']-i['bot']*s))
    return cache[key]
# ---- mikrofon (sel kiri: kepala mic di kiri menghadap kiri)
def keyg(a):
    a=a.astype(np.float32); r,g,b=a[...,0],a[...,1],a[...,2]; d=g-np.maximum(r,b)
    al=np.clip((70-d)/40,0,1); m=np.maximum(r,b); g=np.where(g>m,m+(g-m)*.15,g)
    return Image.fromarray(np.dstack([r,g,b,al*255]).clip(0,255).astype(np.uint8))
M0=keyg(np.asarray(Image.open('mic.jpg').convert('RGB').crop((0,0,500,768))))
_a=np.asarray(M0).astype(np.float32); _a[...,:3]*=np.array([0.9,0.86,0.76]); M0=Image.fromarray(_a.clip(0,255).astype(np.uint8))
CAP=(40,293); BASE_Y=732
SPLIT=480
def mic_for(k):
    c=CH_[k]; i=INFO[f"{c['n']}_{c['idle'][0]}"]; s=c['s']
    mx=c['x']+c.get('sg',1)*(c['mouth'][0]-i['ax'])*s; my=c['y']+(c['mouth'][1]-i['bot'])*s
    ms=0.83
    up=M0.crop((0,0,M0.width,SPLIT)); lo=M0.crop((0,SPLIT,M0.width,M0.height))
    up=up.resize((round(up.width*ms),round(up.height*ms)),Image.NEAREST)
    capy=my+41; top=capy-CAP[1]*ms; floor=c['y']+20
    loh=max(40,int(floor-(top+up.height)))
    lo=lo.resize((up.width,loh),Image.NEAREST)
    m=Image.new('RGBA',(up.width,up.height+loh),(0,0,0,0)); m.alpha_composite(up,(0,0)); m.alpha_composite(lo,(0,up.height))
    if k=='H': px=mx+43-CAP[0]*ms
    else:
        m=m.transpose(Image.FLIP_LEFT_RIGHT); px=mx-43-(m.width-CAP[0]*ms)
    return m,(round(px),round(top))
MICS={k:mic_for(k) for k in CH_}
# bayangan lantai
def shadows():
    amb=Image.new('L',(CW,CH),0); con=Image.new('L',(CW,CH),0); da=ImageDraw.Draw(amb)
    for k,c in CH_.items():
        sp,px,py=sprite(k,c['idle'][0]); al=np.asarray(sp)[...,3]>100
        ys,xs=np.where(al); bot=ys.max(); h=bot-ys.min()
        low=al[int(bot-h*0.30):bot+1]; lx=np.where(low.any(0))[0]
        x0,x1=px+lx.min(),px+lx.max(); fy=py+bot
        # bayangan lembut seluas tapak kursi
        da.ellipse((x0-30,fy-(x1-x0)*0.20,x1+30,fy+(x1-x0)*0.06),fill=150)
        # bayangan kontak: ujung kaki kursi dan sepatu
        strip=al[int(bot-h*0.06):bot+1].astype(np.uint8)*255
        st=Image.fromarray(strip).resize((strip.shape[1],max(4,strip.shape[0]//2)))
        con.paste(Image.new('L',st.size,235),(px,fy-st.height+6),st)
    for k,(m,(px,py)) in MICS.items():
        al=np.asarray(m)[...,3]>100; ys,xs=np.where(al); bot=ys.max()
        row=np.where(al[bot-25:bot+1].any(0))[0]; x0,x1=px+row.min(),px+row.max(); fy=py+bot
        da.ellipse((x0-18,fy-30,x1+18,fy+14),fill=170)
    amb=amb.filter(ImageFilter.GaussianBlur(20)); con=con.filter(ImageFilter.GaussianBlur(6))
    a=np.maximum(np.asarray(amb,np.float32)*0.95,np.asarray(con,np.float32))
    sh=np.zeros((CH,CW,4),np.uint8); sh[...,0]=18; sh[...,1]=14; sh[...,2]=8; sh[...,3]=a.clip(0,255).astype(np.uint8)
    return Image.fromarray(sh,'RGBA')
SH=shadows()
BASE=BG.copy(); BASE.alpha_composite(SH)
# ---- naskah adegan: per baris -> bidikan, pose penutur (gestur, durasi tahan), pose pendengar
E={e['name']:e for e in EV}
def T(n,k='t0'): return E[n][k]
# bidikan: (mulai, jenis)
SHOTS=[(0,'W'),(T('q')+2.2,'H'),(T('q')+3.4,'N'),(T('d1')-0.05,'W'),(T('n2')+0.9,'H'),
       (T('d2'),'H'),(T('s2'),'N'),(T('d3'),'H'),(T('s3'),'N'),(T('d4'),'H'),(T('s4'),'N'),(T('d5'),'H'),(T('s5'),'N'),
       (T('s5','t1')+0.1,'W'),(T('n3'),'N'),(T('d6'),'H'),(T('s6'),'N'),(T('d7'),'H'),(T('s7'),'N'),
       (T('s7','t1')+0.1,'H'),(T('n4'),'N'),(T('d8'),'H'),(T('s8'),'N'),(T('s8','t1')+0.2,'W')]
POSE=[('H',T('d2'),T('d2')+0.9,'20'),
      ('N',T('s2'),T('s2','t1'),'20'),
      ('H',T('d3'),T('d3','t1'),'20'),
      ('N',T('s3'),T('s3','t1'),'30'),
      ('H',T('d5'),T('d5')+1.0,'32'),
      ('N',T('s5'),T('s5')+0.9,'20'),
      ('H',T('L1d'),T('n3')+0.5,'22'),('N',T('L1s'),T('n3')+0.3,'22'),
      ('H',T('d6'),T('d6')+1.2,'21'),
      ('H',T('s6')+0.4,T('d7'),'11'),
      ('N',T('s6'),T('s6')+1.0,'20'),
      ('H',T('d7'),T('d7')+1.1,'21'),
      ('N',T('d7')+0.3,T('s7'),'12'),
      ('H',T('L2d'),T('n4')+0.6,'20'),('N',T('L2s'),T('n4')+0.4,'22'),
      ('H',T('d8'),T('d8')+1.0,'22'),
      ('H',T('L3d'),DUR,'20'),('N',T('s8','t1'),DUR,'22')]
def blink(t,ph): return ((t+ph)%3.7)<0.14
def cell_for(k,t):
    c=CH_[k]; tq=int(t*10)/10.0
    for kk,a,b,cell in POSE:
        if kk==k and a<=t<b: return cell
    e=ENVS[c['key']][min(int(tq*FPS),len(ENVS[c['key']])-1)]
    talking=any(v['spk']==c['key'] and v['t0']<=t<=v['t1'] for v in EV)
    if talking:
        if k=='N' and T('s8')<=t<T('s8','t1'): return '21' if e>0.35 else '22'
        return c['idle'][1] if e>0.35 else c['idle'][0]
    return c['idle'][2] if blink(tq,0.0 if k=='H' else 1.6) else c['idle'][0]
def shot_box(sh,lt):
    z=1+0.015*min(lt,4)/4
    if sh=='W':
        w,h=CW/(1.12*z), CH/(1.12*z); cx,cy=1920,CH/2+80
    else:
        c=CH_[sh]; s=c['s']; i=INFO[f"{c['n']}_{c['idle'][0]}"]
        fx=c['x']+c.get('sg',1)*(c['mouth'][0]-i['ax'])*s; fy=c['y']+(c['mouth'][1]-i['bot'])*s
        h=800/z; w=h*16/9
        cx=fx+(w*0.18 if sh=='H' else -w*0.18); cy=fy+h*0.15
    cx=min(max(cx,w/2),CW-w/2); cy=min(max(cy,h/2),CH-h/2)
    return (cx-w/2,cy-h/2,cx+w/2,cy+h/2)
def render(fr):
    t=fr/FPS
    im=BASE.copy()
    for k in ('H','N'):
        sp,px,py=sprite(k,cell_for(k,t)); im.alpha_composite(sp,(px,py))
    for k,(m,p) in MICS.items(): im.alpha_composite(m,p)
    sh='W'; st=0
    for a,s in SHOTS:
        if t>=a: sh=s; st=a
    box=shot_box(sh,t-st)
    b=tuple(int(round(v)) for v in box)
    out=im.convert('RGB').crop(b).resize((OW,OH),Image.LANCZOS)
    return np.asarray(out)
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='still':
        fs=[float(v) for v in sys.argv[2:]]
        ims=[Image.fromarray(render(int(f*FPS))).resize((640,360)) for f in fs]
        S=Image.new('RGB',(640*2,360*((len(ims)+1)//2)))
        for i,m in enumerate(ims): S.paste(m,((i%2)*640,(i//2)*360))
        S.save('still.jpg'); sys.exit()
    p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{OW}x{OH}','-r',str(FPS),'-i','-','-i','ep3/mix_musik.wav','-map','0:v','-map','1:a','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-shortest','pilar2_like_foto_v3.mp4'],stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for a in pool.imap(render,range(int(DUR*FPS)),chunksize=4): p.stdin.write(a.tobytes())
    p.stdin.close(); p.wait(); print('ok')
