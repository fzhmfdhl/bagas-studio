# Panggung JERSTALK: adegan Jers & Nabila (DIKUNCI) + alat untuk menggambar kartu motion.
# Tampilan kartu TIDAK ada di sini -- dirancang ulang tiap episode, lihat STUDIO_NABILA.md.
import sys,os,math,numpy as np
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from PIL import Image,ImageDraw,ImageFilter,ImageEnhance
from toolkit.studio import font,save_wav,normalize,mix,place,duck,Synth as S,SR,load_wav
W,H,FPS=1080,1920,30
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CX=540;PAPER=(244,242,237);INK=(27,25,31);MUTE=(146,142,138);ACC=(192,80,46);LINE=(214,210,204)
def F(w,s):return font(w,s)
def tw(d,t,f):
    b=d.textbbox((0,0),t,font=f);return b[2]-b[0],b[3]-b[1]
def ctext(d,y,t,f,fill=PAPER,cx=CX):
    w,_=tw(d,t,f);d.text((cx-w//2,y),t,font=f,fill=fill);return w
def wrap(d,t,f,mw):
    o=[];c=''
    for wd in t.split():
        q=(c+' '+wd).strip()
        if tw(d,q,f)[0]<=mw:c=q
        else:
            if c:o.append(c)
            c=wd
    if c:o.append(c)
    return o
def px(im,f=2):return im.resize((im.width//f,im.height//f),Image.NEAREST).resize(im.size,Image.NEAREST)
def grow(im,s):return im.resize((int(im.width*s),int(im.height*s)),Image.NEAREST)
def A(c,a):return (c[0],c[1],c[2],int(max(0,min(1,a))*255))
def ease(x):return 1-(1-max(0.,min(1.,x)))**3

WALL=Image.open(R+'/assets/office/podcast_wall2.png').convert('RGB')
JC=[Image.open(R+'/assets/sprites/jers_c_%d.png'%i) for i in range(3)]
NC=[Image.open(R+'/assets/sprites/nabila_c_%d.png'%i) for i in range(3)]
import glob as _g
ICDIR=os.environ.get('NABILA_ICONS','ic')   # folder PNG hasil `python3 toolkit/lucide.py ic/ "nama:warna" ...`
IC={os.path.basename(p)[:-4]:Image.open(p).convert('RGBA') for p in _g.glob(os.path.join(ICDIR,'*.png'))}

def room(zoom,ox,oy,blur=9):
    w=int(W*zoom);h=int(WALL.height*w/WALL.width)
    b=WALL.resize((w,h),Image.NEAREST).filter(ImageFilter.GaussianBlur(blur))
    im=Image.new('RGB',(W,H),(234,232,228));im.paste(b,(ox,oy))
    if oy+h<H:im.paste(b.crop((0,h-30,w,h)).resize((w,H-(oy+h)),Image.NEAREST),(ox,oy+h))
    return im
BG_J=room(1.55,-300,-170);BG_N=room(1.55,-560,-200)
def shot_j(t,k):
    im=BG_J.copy();j=grow(JC[k],2.2);im.paste(j,(-257,70+int(math.sin(t*2.0)*4)),j);return im
def shot_n(t,k):
    im=BG_N.copy();n=grow(NC[k],2.9)
    im.paste(n,(-336,-579+int(math.sin(t*1.8)*4)),n);return im
def zoomed(im,z,oy=0):
    if z<=1.001 and not oy:return im
    nw,nh=int(W*z),int(H*z);im=im.resize((nw,nh),Image.NEAREST)
    return im.crop(((nw-W)//2,(nh-H)//2+oy,(nw-W)//2+W,(nh-H)//2+oy+H))

# ---------- alat untuk kartu motion ----------
# TIDAK ADA TEMPLATE KARTU di sini. Ini hanya alat: area aman, tema warna,
# penumpuk blok, sapuan, dan pemeriksa kerapian. Tampilan kartu dirancang ulang tiap episode.
TOP,BOT=300,1360
LFT,RGT=96,984
MIDY=(TOP+BOT)//2
GREEN=(42,128,84)

# --- tema warna: tiap konsep motion boleh memakai tema berbeda ---
# Adegan Jers dan Nabila TIDAK terpengaruh tema; ini hanya untuk kartu motion.
TEMA={
 'kertas': dict(paper=(244,242,237),ink=(27,25,31),acc=(192,80,46)),
 'malam':  dict(paper=(22,21,26), ink=(242,240,235),acc=(228,140,60)),
 'biru':   dict(paper=(239,243,249),ink=(16,26,46), acc=(36,84,194)),
 'hutan':  dict(paper=(242,245,239),ink=(20,30,24), acc=(36,120,72)),
 'cetak':  dict(paper=(236,231,222),ink=(30,27,23), acc=(178,50,38)),
 'senja':  dict(paper=(250,244,236),ink=(40,26,30), acc=(206,74,96)),
}
def _mix(a,b,t):return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def pakai_tema(t):
    """t: nama di TEMA, atau dict(paper=,ink=,acc=[,mute=,line=]). Dipanggil sekali sebelum menggambar kartu."""
    global PAPER,INK,ACC,MUTE,LINE,GREEN
    d=TEMA[t] if isinstance(t,str) else dict(t)
    PAPER=tuple(d['paper']);INK=tuple(d['ink']);ACC=tuple(d['acc'])
    MUTE=tuple(d.get('mute') or _mix(INK,PAPER,.46))
    LINE=tuple(d.get('line') or _mix(INK,PAPER,.84))
    GREEN=tuple(d.get('ok') or (42,128,84))
    return dict(paper=PAPER,ink=INK,acc=ACC,mute=MUTE,line=LINE)

def paper(col=None):
    im=Image.new('RGB',(W,H),col or PAPER);ImageDraw.Draw(im).rectangle([0,0,W,16],fill=ACC);return im
def icon(L,key,cx,cy,s,a,rot=0):
    if a<=0 or not key:return
    if key not in IC:
        for suf in ('_ink','_paper','_acc','_mute'):
            if key+suf in IC:key=key+suf;break
    if key not in IC:return
    t=IC[key].resize((s,s),Image.LANCZOS)
    if rot:t=t.rotate(rot,resample=Image.BICUBIC)
    al=t.getchannel('A').point(lambda v:int(v*a));t.putalpha(al)
    L.alpha_composite(t,(cx-s//2,cy-s//2))
def sp_text(t):return ' '.join(t)
def lab(d,y,t,a,cx=CX,col=MUTE,size=34):
    f=F('Medium',size);t=sp_text(t);w,_=tw(d,t,f);d.text((cx-w//2,y),t,font=f,fill=A(col,a))
def rule(d,y,a,w=120,cx=CX,col=ACC,h=4):
    d.rectangle([cx-w//2,y,cx+w//2,y+h],fill=A(col,a))
def fit(d,t,mw,hi,lo=40,weight='Bold',maxlines=3):
    for s in range(hi,lo-1,-4):
        f=F(weight,s);ls=wrap(d,t,f,mw)
        if len(ls)<=maxlines and all(tw(d,l,f)[0]<=mw for l in ls):return f,ls
    f=F(weight,lo);return f,wrap(d,t,f,mw)
def lay(items,top=TOP,bot=BOT,gap=30):
    tot=sum(i[0] for i in items)+gap*(len(items)-1)
    y=top+max(0,((bot-top)-tot)//2);out=[]
    for h,fn in items:out.append((y,h,fn));y+=h+gap
    return out
def draw_stack(L,items,p,top=TOP,bot=BOT,gap=30,st=.10,entr='up'):
    for i,(y,h,fn) in enumerate(lay(items,top,bot,gap)):
        a=ease((p-i*st)*4.5)
        if a<=0:continue
        dx,dy=0,0
        if entr=='up':dy=int((1-a)*26)
        elif entr=='left':dx=int((1-a)*-160)
        elif entr=='right':dx=int((1-a)*160)
        elif entr=='alt':dx=int((1-a)*(-160 if i%2==0 else 160))
        fn(L,y+dy,a,dx)
def _wipe(L,box,p,side,col):
    x0,y0,x1,y1=box;q=ease(min(1,max(0,p)))
    if q<=0:return
    d=ImageDraw.Draw(L)
    if side=='down':d.rectangle([x0,y0,x1,y0+int((y1-y0)*q)],fill=A(col,1))
    elif side=='up':d.rectangle([x0,y1-int((y1-y0)*q),x1,y1],fill=A(col,1))
    elif side=='left':d.rectangle([x1-int((x1-x0)*q),y0,x1,y1],fill=A(col,1))
    else:d.rectangle([x0,y0,x0+int((x1-x0)*q),y1],fill=A(col,1))
def _done(im,L):return Image.alpha_composite(im.convert('RGBA'),L).convert('RGB')
def _mark(d,cx,cy,r,ok,a):
    d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=A(GREEN if ok else ACC,a))
    w=max(5,r//6)
    if ok:
        d.line([(cx-r*.42,cy),(cx-r*.08,cy+r*.36),(cx+r*.46,cy-r*.36)],fill=A(PAPER,a),width=w)
    else:
        d.line([(cx-r*.34,cy-r*.34),(cx+r*.34,cy+r*.34)],fill=A(PAPER,a),width=w)
        d.line([(cx-r*.34,cy+r*.34),(cx+r*.34,cy-r*.34)],fill=A(PAPER,a),width=w)

def cek_kartu(im,nama=''):
    """Jaga kerapian. Isi = piksel yang menyimpang dari warna barisnya DAN kolomnya,
    jadi blok warna penuh (pita, layar terbelah) tidak dihitung sebagai isi."""
    import numpy as _np
    a=_np.asarray(im.convert('L')).astype(int)[20:]
    mr=_np.abs(a-_np.median(a,axis=1,keepdims=True))>26
    mc=_np.abs(a-_np.median(a,axis=0,keepdims=True))>26
    m=mr&mc;off=20;bad=[]
    if m[:max(0,TOP-40-off)].any():bad.append('isi di atas area aman')
    if m[max(0,BOT+40-off):].any():bad.append('isi di bawah area aman')
    if m[:,:LFT-40].any():bad.append('isi melewati tepi kiri')
    if m[:,RGT+40:].any():bad.append('isi melewati tepi kanan')
    ys,xs=_np.where(m)
    if not len(ys):bad.append('kartu kosong')
    else:
        isi=(ys.max()-ys.min())/(BOT-TOP)
        if isi<.45:bad.append('isi cuma %d%% tinggi area aman (minimal 45%%)'%int(isi*100))
    if bad:raise AssertionError('kartu %s: %s'%(nama,'; '.join(bad)))
    return True
