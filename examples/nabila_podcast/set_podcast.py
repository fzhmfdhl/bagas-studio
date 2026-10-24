# Set podcast pixel Nabila: shot, potongan kamera, dan sistem kartu motion.
# PATOKAN TETAP. Semua kartu dipusatkan di x=540 dan blok isinya di sekitar y=800.
# Yang berganti tiap episode hanya ISI kartu dan pilihan ikon Lucide.
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

# ---------- kartu motion ----------
def paper():
    im=Image.new('RGB',(W,H),PAPER);d=ImageDraw.Draw(im);d.rectangle([0,0,W,16],fill=ACC);return im
def icon(L,key,cx,cy,s,a):
    """Ikon Lucide, rata tengah di (cx,cy), tanpa kotak."""
    if a<=0 or key not in IC:return
    t=IC[key].resize((s,s),Image.LANCZOS)
    al=t.getchannel('A').point(lambda v:int(v*a))
    t.putalpha(al)
    L.alpha_composite(t,(cx-s//2,cy-s//2))
def lab(d,y,t,a,cx=CX):
    f=F('Medium',32);w,_=tw(d,t,f);d.text((cx-w//2,y),t,font=f,fill=A(MUTE,a))
def rule(d,y,a,w=96,cx=CX,col=ACC):
    d.rectangle([cx-w//2,y,cx+w//2,y+3],fill=A(col,a))

def c_title(p,title,sub,brand='JERSTALK'):
    """Kartu pembuka. Pertanyaan pertama Nabila terdengar di atas kartu ini (lihat rakit_episode.py)."""
    im=paper();L=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(L)
    a0=ease(p*4)
    icon(L,'mic_ink',CX,544,150,a0);d=ImageDraw.Draw(L)
    fb=F('Bold',52);wb,_=tw(d,brand,fb)
    d.text((CX-wb//2,668),brand,font=fb,fill=A(INK,a0))
    rule(d,752,a0)
    f=F('Bold',92);lines=wrap(d,title,f,660);y=824
    for i2,l in enumerate(lines):
        a=ease((p-.1-i2*.09)*4.5)
        if a>0:ctext(d,y+int((1-a)*22),l,f,A(INK,a))
        y+=108
    a2=ease((p-.4)*4)
    if a2>0:ctext(d,y+30,sub,F('Medium',32),A(MUTE,a2))
    return Image.alpha_composite(im.convert('RGBA'),L).convert('RGB')

def c_statement(p,eyebrow,w1,w2,ic,dark=False):
    im=Image.new('RGB',(W,H),INK if dark else PAPER)
    ImageDraw.Draw(im).rectangle([0,0,W,16],fill=ACC)
    L=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(L)
    a0=ease(p*4.5)
    icon(L,ic,CX,536,190,a0);d=ImageDraw.Draw(L)
    lab(d,690,eyebrow,a0);rule(d,754,a0)
    f=F('Bold',104)
    a1=ease((p-.14)*4.5);a2=ease((p-.26)*4.5)
    if a1>0:ctext(d,824+int((1-a1)*22),w1,f,A(PAPER if dark else INK,a1))
    if a2>0:ctext(d,940+int((1-a2)*22),w2,f,A(ACC,a2))
    return Image.alpha_composite(im.convert('RGBA'),L).convert('RGB')

def c_steps(p,eyebrow,rows):
    """Daftar bertahap. Tiap baris dipusatkan sebagai satu kesatuan ikon+teks."""
    im=paper();L=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(L)
    a0=ease(p*4.5);lab(d,480,eyebrow,a0);rule(d,544,a0)
    f=F('Bold',50);IS,GAPX=78,26
    ws=[tw(d,t,f)[0] for _,t in rows]
    y=646
    for i2,(ic,t) in enumerate(rows):
        a=ease((p-.12-i2*.15)*4.5)
        if a<=0:
            y+=164;continue
        dy=int((1-a)*22);tot=IS+GAPX+ws[i2];x0=CX-tot//2
        icon(L,ic,x0+IS//2,y+dy+44,IS,a);d=ImageDraw.Draw(L)
        d.text((x0+IS+GAPX,y+dy+16),t,font=f,fill=A(INK,a))
        if i2<len(rows)-1:d.rectangle([CX-300,y+dy+120,CX+300,y+dy+121],fill=A(LINE,a))
        y+=164
    return Image.alpha_composite(im.convert('RGBA'),L).convert('RGB')

def c_two(p,eyebrow,left,right):
    im=paper();L=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(L)
    a0=ease(p*4.5);lab(d,556,eyebrow,a0);rule(d,620,a0)
    for i2,(ic,t) in enumerate([left,right]):
        a=ease((p-.14-i2*.16)*4.5)
        if a<=0:continue
        cx=CX-190+i2*380;dy=int((1-a)*22)
        icon(L,ic,cx,744+dy,132,a);d=ImageDraw.Draw(L)
        for j,l in enumerate(wrap(d,t,F('Bold',44),320)[:2]):
            ctext(d,844+dy+j*52,l,F('Bold',44),A(INK,a),cx=cx)
    a2=ease((p-.5)*4)
    if a2>0:
        d=ImageDraw.Draw(L)
        d.ellipse([CX-32,712,CX+32,776],fill=A(ACC,a2))
        ctext(d,722,'=',F('Bold',42),A(PAPER,a2))
    return Image.alpha_composite(im.convert('RGBA'),L).convert('RGB')

def c_three(p,eyebrow,words,icons):
    im=paper();L=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(L)
    a0=ease(p*4.5);lab(d,576,eyebrow,a0);rule(d,640,a0)
    for i2,wd in enumerate(words):
        a=ease((p-.12-i2*.18)*5)
        if a<=0:continue
        cx=CX-250+i2*250;dy=int((1-a)*22)
        icon(L,icons[i2],cx,770+dy,116,a);d=ImageDraw.Draw(L)
        ctext(d,866+dy,wd,F('Bold',48),A(INK,a),cx=cx)
        if i2<2:
            d.polygon([(cx+106,812+dy),(cx+134,826+dy),(cx+106,840+dy)],fill=A(LINE,a))
    return Image.alpha_composite(im.convert('RGBA'),L).convert('RGB')

def c_end(p,bg):
    im=Image.blend(bg,Image.new('RGB',(W,H),PAPER),min(1,ease(p*2.6))*.94)
    ImageDraw.Draw(im).rectangle([0,0,W,16],fill=ACC)
    L=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(L)
    q=max(0,(p-.2)/.8);a0=ease(q*3)
    icon(L,'store_ink',CX,572,120,a0);d=ImageDraw.Draw(L)
    f=F('Bold',72)
    for i2,l in enumerate(['Tulis usahamu','di komentar']):
        a=ease((q-i2*.1)*4)
        if a>0:ctext(d,680+i2*92+int((1-a)*22),l,f,A(INK,a))
    rule(d,884,a0)
    a2=ease((q-.35)*4)
    if a2>0:
        ctext(d,940,'nanti aku bedah satu',F('Medium',42),A(MUTE,a2))
        t='@jerapahmerah_';fw=F('Bold',38);w,_=tw(d,t,fw)
        d.rounded_rectangle([CX-w//2-34,1030,CX+w//2+34,1106],26,outline=A(ACC,a2),width=4)
        ctext(d,1050,t,fw,A(ACC,a2))
    return Image.alpha_composite(im.convert('RGBA'),L).convert('RGB')

