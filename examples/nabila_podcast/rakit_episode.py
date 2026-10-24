# Contoh perakitan satu episode: potong suara per baris, jalin dialog, potongan kamera, musik ducking.
import sys,os,math,numpy as np
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'set_podcast.py')).read().split("SEG=[('open'")[0])
from toolkit.studio import voice_segments,save_wav,normalize,mix,place,duck,Synth as S,SR
JL=['Chat pelanggan numpuk tiap malam, terus kamu balas pagi-pagi.','Nah itu. Telat balas itu diam-diam makan omzet.','Kumpulkan chat lama kamu, kasih ke AI, minta dia bikin draft balasan.','Betul. Kamu tinggal baca, benerin sedikit, kirim.','Kalau mau aku bedah punya kamu, tulis di komentar.']
NL=['Dan pas kamu balas, orangnya udah beli di tempat lain.','Terus solusinya apa?','Jadi nggak ngetik dari nol tiap kali.','Dan nada bicaranya tetap kamu.']
SJ=voice_segments('voJ.wav',JL);SN=voice_segments('voN.wav',NL)
print('durasi J',[round(x['dur'],2) for x in SJ]);print('durasi N',[round(x['dur'],2) for x in SN])
# urutan dialog: (siapa, indeks, kartu motion yang menimpa)
ORDER=[('J',0,None),('N',0,None),('J',1,'A'),('N',1,None),('J',2,'B'),('N',2,None),('J',3,None),('N',3,None),('J',4,'E')]
OPEN=2.6;GAP=.26
cues=[];t=OPEN
for who,i,kart in ORDER:
    seg=(SJ if who=='J' else SN)[i]
    cues.append({'who':who,'i':i,'a':t,'b':t+seg['dur'],'card':kart,'aud':seg['audio']})
    t+=seg['dur']+GAP
TAIL=1.9;DUR=t+TAIL
print('total',round(DUR,2))
# ---- audio ----
n=int(DUR*SR);voice=np.zeros(n)
for c in cues:place(voice,c['aud'],c['a'])
bed=np.zeros(n);perc=np.zeros(n);root=[48,48,53,46]
for i in range(int(DUR/1.6)+1):
    tt=i*1.6;m=root[i%4]
    place(bed,S.lowpass(S.note('tri',m,1.7,vol=.05,a=.2,r=.5),12),tt)
    place(bed,S.lowpass(S.note('tri',m+12,1.7,vol=.02,a=.3,r=.6),9),tt)
for i in range(int(DUR/.4)+1):
    tt=i*.4
    if i%4==0:place(perc,S.kick(.10),tt)
    if i%2==1:place(perc,S.hat(.018),tt)
music=duck(mix(bed,perc),[(c['a'],c['b']) for c in cues],depth=.42)
save_wav('ep6.wav',normalize(mix(normalize(voice,.92),music),.93))
# ---- video ----
FPS=30;N=int(DUR*FPS);os.makedirs('f6',exist_ok=True)
def at(t):
    for c in cues:
        if c['a']-GAP/2<=t<c['b']+GAP/2:return c
    return None
for fi in range(N):
    t=fi/FPS
    if t<OPEN:
        im=m_open(min(1,t/ (OPEN*.75)))
    else:
        c=at(t)
        if c is None:
            im=m_end(1.0) if t>cues[-1]['b'] else shot_j(t,2)
        else:
            p=(t-c['a'])/max(.01,c['b']-c['a'])
            if c['card']=='A' and p>.12:im=m_a(min(1,(p-.12)/.5))
            elif c['card']=='B' and p>.10:im=m_b(min(1,(p-.10)/.55))
            elif c['card']=='E' and p>.30:im=m_end(min(1,(p-.30)/.6))
            else:
                k=int((t-c['a'])/.42)%2
                if c['who']=='J':im=zoomed(shot_j(t,k),1.0+p*.035,int(p*-12))
                else:im=zoomed(shot_n(t,k),1.0+p*.03,int(p*-8))
    px(im,2).save('f6/%04d.png'%fi)
print('frames',N)
