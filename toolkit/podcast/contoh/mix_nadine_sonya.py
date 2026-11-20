import numpy as np, wave, json, scipy.io.wavfile as wf
from scipy.signal import butter,lfilter
SR=44100; FPS=24
def load(p):
    w=wave.open(p); return np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
def cut(a,s,e=None,th=-60,pad=0.03):
    e=len(a)/SR if e is None else e
    x=a[int(s*SR):int(e*SR)]; h=int(SR*0.01); n=len(x)//h
    db=20*np.log10(np.array([np.sqrt((x[i*h:(i+1)*h]**2).mean())+1e-9 for i in range(n)]))
    idx=np.where(db>th)[0]; i0=max(0,idx[0]*h-int(pad*SR)); i1=min(len(x),(idx[-1]+1)*h+int(pad*SR))
    return x[i0:i1].copy()
def norm(a,t=-20):
    a=a*(10**(t/20)/(np.sqrt((a**2).mean())+1e-9)); pk=np.abs(a).max(); return a*(0.89/pk) if pk>0.89 else a
def fade(a,d=0.25):
    a=a.copy(); n=min(len(a),int(d*SR)); a[-n:]*=np.linspace(1,0,n); return a
N=load('ep3/N.wav'); D=load('ep3/D.wav'); S=load('ep3/S.wav')
q=cut(N,0,4.55); n2=cut(N,4.6,7.1); n3=cut(N,7.2,8.9); n4=cut(N,8.95)
d=[cut(D,a,b) for a,b in [(0,1.15),(1.3,3.1),(3.25,5.55),(5.62,6.75),(6.8,9.1),(9.15,12.1),(12.15,15.2),(15.3,None)]]
s=[cut(S,a,b) for a,b in [(0,0.8),(0.86,2.1),(2.2,3.82),(3.9,4.5),(4.55,6.32),(6.36,9.8),(9.85,12.58),(12.6,None)]]
dl=fade(cut(load('ep3/Dl.wav'),0,None),0.4)
ST=load('lz/ST0.wav'); sA=fade(ST[int(2.10*SR):int(3.44*SR)].copy(),0.25); sB=fade(ST[int(3.92*SR):int(5.14*SR)].copy(),0.3)
LN0=load('lz/N0.wav'); n0=fade(cut(LN0,0.05,3.25),0.5); n0a=fade(cut(LN0,0.05,1.6),0.35)
ev=[]; tracks={'N':[], 'S':[], 'D':[]}
def put(spk,a,t,kind='talk',gain=1.0,name=''):
    a=norm(a)*gain
    if spk=='N':
        b_,a_=butter(2,3800/(SR/2)); a=lfilter(b_,a_,a).astype(np.float32)*0.42
    tracks[spk].append((int(t*SR),a)); dd=len(a)/SR
    ev.append(dict(spk=spk,t0=t,t1=t+dd,kind=kind,name=name)); return t+dd
t=0.4
t=put('N',q,t,name='q')
e1=put('D',d[0],t+0.12,name='d1'); e2=put('S',s[0],t+0.20,name='s1')
t=put('N',n2,max(e1,e2)+0.08,name='n2')
t=put('D',d[1],t+0.10,name='d2')
t=put('S',s[1],t-0.08,name='s2')
t=put('D',d[2],t+0.02,name='d3')
t=put('S',s[2],t-0.15,name='s3')
t=put('D',d[3],t+0.02,name='d4')
t=put('S',s[3],t-0.08,name='s4')
t=put('D',d[4],t+0.05,name='d5')
t=put('S',s[4],t+0.08,name='s5')
put('D',dl,t-0.10,kind='laugh',gain=0.55,name='L1d'); put('N',n0a,t+0.0,kind='laugh',gain=0.8,name='L1n'); put('S',sB,t+0.15,kind='laugh',gain=0.5,name='L1s')
t=put('N',n3,t+1.35,name='n3')
t=put('D',d[5],t-0.05,name='d6')
t=put('S',s[5],t+0.05,name='s6')
t=put('D',d[6],t-0.12,name='d7')
t=put('S',s[6],t+0.05,name='s7')
put('D',dl,t-0.05,kind='laugh',gain=0.55,name='L2d'); put('N',n0a,t+0.05,kind='laugh',gain=0.8,name='L2n'); put('S',sA,t+0.30,kind='laugh',gain=0.5,name='L2s')
t=put('N',n4,t+1.45,name='n4')
t=put('D',d[7],t+0.0,name='d8')
t=put('S',s[7],t-0.20,name='s8')
put('D',dl,t-0.15,kind='laugh',gain=0.6,name='L3d'); put('N',n0,t-0.05,kind='laugh',gain=0.8,name='L3n'); put('S',sB,t+0.05,kind='laugh',gain=0.6,name='L3s')
total=max(e['t1'] for e in ev)-0.2
n=int(total*SR); mix=np.zeros(n,np.float32); envs={}
h=SR//FPS; nf=int(total*FPS)
for k,parts in tracks.items():
    tr=np.zeros(n+SR*6,np.float32)
    for i0,a in parts: tr[i0:i0+len(a)]+=a
    tr=tr[:n]; mix+=tr
    e=np.array([np.sqrt((tr[f*h:(f+1)*h]**2).mean()) for f in range(nf)])
    envs[k]=np.clip(e/0.09,0,1.5).tolist()
fo=int(0.9*SR); mix[-fo:]*=np.linspace(1,0,fo)
mix*=0.9/np.abs(mix).max()
wf.write('ep3/mix.wav',SR,(mix*32767).astype(np.int16))
json.dump(dict(ev=ev,total=total,envs=envs),open('ep3/tl.json','w'))
for e in ev: print(e['name'],e['spk'],round(e['t0'],2),round(e['t1'],2))
print('total',round(total,2))
