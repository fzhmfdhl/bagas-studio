# Contoh set podcast pixel Nabila -- koordinat set WAJIB dipakai ulang, bagian motion diganti tiap episode.
import sys,os,math
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from PIL import Image,ImageDraw,ImageFilter
from toolkit.studio import sprite,font
W,H,FPS=1080,1920,30
INK=(16,14,22);CREAM=(246,240,228);WARM=(255,138,61);NEON=(255,86,52)
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def F(w,s):return font(w,s)
def tw(d,t,f):
    b=d.textbbox((0,0),t,font=f);return b[2]-b[0],b[3]-b[1]
def ctext(d,y,t,f,fill=CREAM,out=None,ow=6,cx=470):
    w,h=tw(d,t,f);x=cx-w//2
    if out:
        for dx in range(-ow,ow+1,2):
            for dy in range(-ow,ow+1,2):
                if dx*dx+dy*dy<=ow*ow:d.text((x+dx,y+dy),t,font=f,fill=out)
    d.text((x,y),t,font=f,fill=fill);return w
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
def px(im,f=2):
    return im.resize((im.width//f,im.height//f),Image.NEAREST).resize(im.size,Image.NEAREST)

# ---------- aset ----------
WALL=Image.open(ROOT+'/assets/office/podcast_wall.png').convert('RGB')
WALL=WALL.resize((W,int(WALL.height*W/WALL.width)),Image.NEAREST)
JERS=[Image.open(ROOT+'/assets/sprites/jers_t_%d.png'%i) for i in range(4)]
JS=1.0
JERS=[j.resize((int(j.width*JS),int(j.height*JS)),Image.NEAREST) for j in JERS]
NAB,_,_=sprite('nabila_h_0')
NFH=846
NAB=NAB.resize((int(NAB.width*NFH/NAB.height),NFH),Image.NEAREST)
NABW=NAB.crop((0,0,NAB.width,int(NFH*.47)))
DESK=1342
JX,JBOT=46,1378
NX,NBOT=636,1374

def base():
    im=Image.new('RGB',(W,H),INK)
    im.paste(WALL,(0,0))
    d=ImageDraw.Draw(im)
    d.rectangle([0,DESK,W,H],fill=(46,30,20))
    d.rectangle([0,DESK,W,DESK+30],fill=(120,84,50))
    d.rectangle([0,DESK+30,W,DESK+42],fill=(70,46,26))
    for x in range(0,W,26):d.line([(x,DESK+42),(x,H)],fill=(40,26,17),width=2)
    for x in range(0,W,26):d.line([(x+9,DESK+42),(x+9,H)],fill=(53,35,22),width=1)
    # benda di atas meja
    d.rounded_rectangle([408,DESK-96,560,DESK-4],8,fill=(26,28,36),outline=(86,94,112),width=3)
    d.rectangle([424,DESK-82,544,DESK-30],fill=(22,44,56))
    for i in range(4):d.line([(432,DESK-72+i*12),(432+56+i*14,DESK-72+i*12)],fill=(90,200,250),width=3)
    d.rounded_rectangle([586,DESK-66,640,DESK-4],7,fill=(50,38,30),outline=(104,80,58),width=3)
    d.ellipse([588,DESK-70,638,DESK-56],fill=(78,56,40))
    d.rounded_rectangle([916,DESK-78,1032,DESK-4],8,fill=(24,26,34),outline=(80,88,106),width=3)
    for i in range(3):
        x=934+i*32
        d.rectangle([x,DESK-62,x+16,DESK-20],fill=(40,44,56))
        d.rectangle([x,DESK-62+i*10,x+16,DESK-56+i*10],fill=(255,138,61))
    d.arc([120,DESK-20,300,DESK+40],180,360,fill=(34,24,18),width=5)
    sh=Image.new('RGB',(W,H),(0,0,0));sd=ImageDraw.Draw(sh)
    sd.rectangle([0,DESK-60,W,DESK],fill=(30,20,14))
    im=Image.blend(im,im,0)
    return im
BG=base()

def mic(d,cx,top,sc=1.0):
    s=lambda v:int(v*sc)
    d.rectangle([cx-s(7),top+s(62),cx+s(7),top+s(150)],fill=(38,40,50))
    d.rectangle([cx-s(34),top+s(146),cx+s(34),top+s(162)],fill=(46,48,60))
    d.rounded_rectangle([cx-s(36),top,cx+s(36),top+s(74)],s(22),fill=(28,30,38),outline=(104,112,130),width=3)
    for i in range(5):
        y=top+s(12)+i*s(13)
        d.line([(cx-s(26),y),(cx+s(26),y)],fill=(78,86,104),width=2)

def scene(t,talk,gest):
    im=BG.copy()
    if talk:
        k=gest[int(t*6)%len(gest)]
    else:
        k=gest[0]
    j=JERS[k]
    bob=int(math.sin(t*2.2)*2)
    im.paste(j,(JX,JBOT-j.height+bob),j)
    nb=int(math.sin(t*1.7)*3)+int(math.sin(t*.6)*2)
    im.paste(NABW,(NX,NBOT-NABW.height+nb),NABW)
    d=ImageDraw.Draw(im,'RGBA')
    mic(d,300,1150,1.0)
    mic(d,792,1182,.84)
    # kilau neon lembut di wajah
    gl=Image.new('RGB',(W,H),(0,0,0));gd=ImageDraw.Draw(gl)
    gd.ellipse([180,560,900,1120],fill=(44,16,10))
    gl=gl.filter(ImageFilter.GaussianBlur(120))
    im=Image.blend(im,Image.new('RGB',(W,H),(255,120,80)),0)
    return im

def zoomed(im,z,ox=0,oy=0):
    if z<=1.001 and not ox and not oy:return im
    nw,nh=int(W*z),int(H*z)
    im=im.resize((nw,nh),Image.NEAREST)
    x=(nw-W)//2+ox;y=(nh-H)//2+oy
    return im.crop((x,y,x+W,y+H))

# ---------- bagian motion (satu-satunya tempat teks) ----------
def m_open(p):
    im=BG.copy().filter(ImageFilter.GaussianBlur(7))
    im=Image.blend(im,Image.new('RGB',(W,H),(10,8,14)),.72);d=ImageDraw.Draw(im)
    a=min(1.,p*3)
    d.rounded_rectangle([60,660,880,1020],26,fill=(22,18,30),outline=NEON,width=5)
    ctext(d,700,'PODCAST PIXEL',F('Medium',40),fill=(255,150,110))
    f=F('Bold',92);L=wrap(d,'Balas Chat Lebih Cepat',f,740)
    y=780
    for i,l in enumerate(L):
        if p*3>i*.3:ctext(d,y,l,f,fill=CREAM)
        y+=104
    if p>.5:ctext(d,1060,'bisnis & AI  ·  EP 00',F('Medium',38),fill=(150,140,160))
    return im
def m_a(p):
    im=Image.new('RGB',(W,H),(226,71,43));d=ImageDraw.Draw(im)
    for y in range(0,H,8):d.line([(0,y),(W,y)],fill=(236,86,58),width=3)
    f=F('Bold',128)
    y=560
    for i,wd in enumerate(['TELAT','BALAS','=','ORDER','HILANG']):
        a=max(0.,min(1.,(p-i*.1)*7))
        if a<=0:continue
        ctext(d,y,wd,f,fill=(255,247,236) if wd!='=' else (255,206,120),cx=470+int((1-a)*240))
        y+=148
    return im
def m_b(p):
    im=Image.new('RGB',(W,H),(13,11,18));d=ImageDraw.Draw(im)
    for x in range(0,W,54):d.line([(x,0),(x,H)],fill=(21,18,28),width=2)
    ctext(d,430,'3 LANGKAH',F('Bold',96),fill=CREAM)
    for i,(n,t) in enumerate([('1','Kumpulkan chat lama'),('2','Minta AI buat draft'),('3','Kamu baca, kirim')]):
        a=max(0.,min(1.,(p-i*.16)*5))
        if a<=0:continue
        y=640+i*200;dy=int((1-a)*60)
        d.rounded_rectangle([60,y+dy,880,y+150+dy],18,fill=(24,20,32),outline=(84,70,104),width=3)
        d.ellipse([92,y+34+dy,172,y+114+dy],fill=WARM)
        ctext(d,y+50+dy,n,F('Bold',58),fill=(20,16,12),cx=132)
        d.text((202,y+48+dy),t,font=F('Medium',48),fill=CREAM)
    return im
def m_end(p):
    im=scene(22.0,False,[3])
    d=ImageDraw.Draw(im,'RGBA')
    d.rectangle([0,0,W,H],fill=(10,8,14,int(min(1,p*2.4)*205)))
    d=ImageDraw.Draw(im)
    ctext(d,600,'Mau aku bedah punyamu?',F('Bold',66),fill=CREAM)
    ctext(d,696,'tulis di komentar',F('Medium',48),fill=WARM)
    if p>.45:
        d.rounded_rectangle([296,800,644,876],20,outline=NEON,width=4)
        ctext(d,820,'@jerapahmerah_',F('Bold',40),fill=(255,150,110))
    return im

SEG=[('open',0.0,2.8),('talk',2.8,6.4),('cutA',6.4,9.0),('talk',9.0,13.2),
     ('cutB',13.2,16.6),('talk',16.6,20.2),('end',20.2,23.6)]
GEST={0:[0,1],1:[2,0],2:[3,1]}
DUR=SEG[-1][2];N=int(DUR*FPS)
os.makedirs('f2',exist_ok=True)
ti=0
for i in range(N):
    t=i/FPS
    s=[x for x in SEG if x[1]<=t<x[2]] or [SEG[-1]]
    k,a,b=s[0];p=(t-a)/(b-a)
    if k=='open':im=m_open(p)
    elif k=='cutA':im=m_a(p)
    elif k=='cutB':im=m_b(p)
    elif k=='end':im=m_end(p)
    else:
        idx=[x for x in SEG if x[0]=='talk'].index(s[0])
        im=scene(t,True,GEST[idx])
        im=zoomed(im,1.0+p*.045,0,int(p*-18))
    im=px(im,2)
    im.save('f2/%04d.png'%i)
print('frames',N)
