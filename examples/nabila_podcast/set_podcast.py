# Set podcast pixel Nabila: koordinat, potongan kamera, dan sistem kartu motion.
# PATOKAN TETAP -- pakai apa adanya; yang berganti tiap episode hanya ISI kartu.
import sys,os,math
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from PIL import Image,ImageDraw,ImageFilter,ImageEnhance
from toolkit.studio import font
W,H,FPS=1080,1920,30
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CX=540                      # titik tengah sejati
PAPER=(244,242,237);INK=(27,25,31);MUTE=(146,142,138);ACC=(192,80,46)
def F(w,s):return font(w,s)
def tw(d,t,f):
    b=d.textbbox((0,0),t,font=f);return b[2]-b[0],b[3]-b[1]
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

def room(zoom,ox,oy,blur=9,bright=1.0):
    w=int(W*zoom);h=int(WALL.height*w/WALL.width)
    b=WALL.resize((w,h),Image.NEAREST).filter(ImageFilter.GaussianBlur(blur))
    if bright!=1.0:b=ImageEnhance.Brightness(b).enhance(bright)
    im=Image.new('RGB',(W,H),(234,232,228));im.paste(b,(ox,oy))
    if oy+h<H:
        im.paste(b.crop((0,h-30,w,h)).resize((w,H-(oy+h)),Image.NEAREST),(ox,oy+h))
    return im
BG_J=room(1.55,-300,-170)
BG_N=room(1.55,-560,-200)

def shot_j(t,k):
    im=BG_J.copy();j=grow(JC[k],2.2)
    im.paste(j,(-257,70+int(math.sin(t*2.0)*4)),j);return im
def shot_n(t,k):
    im=BG_N.copy();n=grow(NC[k],2.45)
    nod=int(max(0,math.sin(t*2.4))*9)
    im.paste(n,(-538,116+int(math.sin(t*1.8)*4)+nod),n);return im
def zoomed(im,z,oy=0):
    if z<=1.001 and not oy:return im
    nw,nh=int(W*z),int(H*z);im=im.resize((nw,nh),Image.NEAREST)
    return im.crop(((nw-W)//2,(nh-H)//2+oy,(nw-W)//2+W,(nh-H)//2+oy+H))

# ---------------- kartu motion: bersih, di tengah, satu aksen ----------------
def card(p,zoom=True):
    im=Image.new('RGB',(W,H),PAPER)
    d=ImageDraw.Draw(im)
    d.rectangle([0,0,W,16],fill=ACC)
    return im,ImageDraw.Draw(Image.new('RGBA',(W,H),(0,0,0,0)))
def stack(im,items,p,top):
    """items: (jenis, isi, font, warna, tinggi). Naik + pudar berurutan, rata tengah di CX."""
    L=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(L)
    y=top
    for i,(kind,val,f,col,h) in enumerate(items):
        a=ease((p-i*.09)*4.5)
        dy=int((1-a)*22)
        if a>0:
            if kind=='t':
                w,_=tw(d,val,f);d.text((CX-w//2,y+dy),val,font=f,fill=A(col,a))
            elif kind=='rule':
                d.rectangle([CX-val//2,y+dy,CX+val//2,y+dy+3],fill=A(col,a))
            elif kind=='pill':
                w,_=tw(d,val,f)
                d.rounded_rectangle([CX-w//2-34,y+dy-18,CX+w//2+34,y+dy+h-16],26,outline=A(col,a),width=4)
                d.text((CX-w//2,y+dy),val,font=f,fill=A(col,a))
        y+=h
    return Image.alpha_composite(im.convert('RGBA'),L).convert('RGB')

def m_open(p):
    im,_=card(p)
    f1=F('Medium',32);f2=F('Bold',94)
    d=ImageDraw.Draw(im)
    L=wrap(d,'Balas Chat Lebih Cepat',f2,660)
    items=[('t','PODCAST PIXEL',f1,MUTE,58),('rule',96,None,ACC,46)]
    for l in L:items.append(('t',l,f2,INK,108))
    items.append(('rule',0,None,ACC,30))
    items.append(('t','bisnis & AI  ·  EP 00',F('Medium',30),MUTE,40))
    top=820-sum(x[4] for x in items)//2
    return stack(im,items,p,top)

def m_a(p):
    im=Image.new('RGB',(W,H),INK);d=ImageDraw.Draw(im)
    d.rectangle([0,0,W,16],fill=ACC)
    f=F('Bold',112);fs=F('Medium',32)
    items=[('t','TELAT BALAS',fs,(176,170,166),54),('rule',96,None,ACC,54),
           ('t','Order',f,PAPER,126),('t','hilang',f,ACC,126),
           ('rule',0,None,ACC,34),('t','tanpa kamu sadar',F('Medium',38),(176,170,166),48)]
    top=820-sum(x[4] for x in items)//2
    return stack(im,items,p,top)

def m_b(p):
    im,_=card(p);d=ImageDraw.Draw(im)
    f1=F('Medium',32);f2=F('Bold',52);f3=F('Bold',40)
    L=Image.new('RGBA',(W,H),(0,0,0,0));dd=ImageDraw.Draw(L)
    a0=ease(p*5)
    w,_=tw(dd,'3 LANGKAH',f1)
    dd.text((CX-w//2,int(520+(1-a0)*20)),'3 LANGKAH',font=f1,fill=A(MUTE,a0))
    dd.rectangle([CX-48,590,CX+48,593],fill=A(ACC,a0))
    rows=[('01','Kumpulkan chat lama'),('02','Minta AI buat draft'),('03','Kamu baca, kirim')]
    y=692
    for i,(n,t) in enumerate(rows):
        a=ease((p-.12-i*.13)*4.5);dy=int((1-a)*20)
        if a>0:
            dd.text((CX-330,y+dy+12),n,font=f3,fill=A(ACC,a))
            dd.text((CX-220,y+dy),t,font=f2,fill=A(INK,a))
            if i<2:dd.rectangle([CX-330,y+dy+96,CX+330,y+dy+97],fill=A((214,210,204),a))
        y+=130
    return Image.alpha_composite(im.convert('RGBA'),L).convert('RGB')

def m_end(p):
    im=shot_j(27.0,0)
    im=Image.blend(im,Image.new('RGB',(W,H),PAPER),min(1,ease(p*2.6))*.93)
    d=ImageDraw.Draw(im);d.rectangle([0,0,W,16],fill=ACC)
    items=[('t','Mau aku bedah',F('Bold',72),INK,86),('t','punyamu?',F('Bold',72),INK,96),
           ('rule',96,None,ACC,52),('t','tulis di komentar',F('Medium',42),MUTE,92),
           ('pill','@jerapahmerah_',F('Bold',38),ACC,72)]
    top=820-sum(x[4] for x in items)//2
    return stack(im,items,max(0,(p-.25)/.75),top)

SEG=[('open',0.0,3.0),('J',3.0,7.2),('N',7.2,8.4),('J',8.4,11.4),('cutA',11.4,14.2),
     ('J',14.2,18.0),('N',18.0,19.1),('J',19.1,22.2),('cutB',22.2,25.8),('J',25.8,27.8),('end',27.8,31.0)]
DUR=SEG[-1][2];N=int(DUR*FPS)
os.makedirs('f5',exist_ok=True)
for i in range(N):
    t=i/FPS
    s=[x for x in SEG if x[1]<=t<x[2]] or [SEG[-1]]
    kind,a,b=s[0];p=(t-a)/(b-a)
    if kind=='open':im=m_open(p)
    elif kind=='cutA':im=m_a(p)
    elif kind=='cutB':im=m_b(p)
    elif kind=='end':im=m_end(p)
    elif kind=='N':im=zoomed(shot_n(t,2 if p<.55 else 0),1.0+p*.03)
    else:
        k=2 if p>.9 else int((t-a)/.45)%2
        im=zoomed(shot_j(t,k),1.0+p*.035,int(p*-12))
    px(im,2).save('f5/%04d.png'%i)
print('frames',N)
