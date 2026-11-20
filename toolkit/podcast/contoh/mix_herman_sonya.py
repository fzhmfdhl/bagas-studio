import numpy as np, wave, json, scipy.io.wavfile as wf
SR=44100; FPS=24
def load(p):
    w=wave.open(p); return np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
def cut(a,s,e,th=-45,pad=0.03):
    x=a[int(s*SR):int(e*SR)]; h=int(SR*0.01); n=len(x)//h
    db=20*np.log10(np.array([np.sqrt((x[i*h:(i+1)*h]**2).mean())+1e-9 for i in range(n)]))
    idx=np.where(db>th)[0]; i0=max(0,idx[0]*h-int(pad*SR)); i1=min(len(x),(idx[-1]+1)*h+int(pad*SR))
    return x[i0:i1].copy(), s+i0/SR
def norm(a,t=-20):
    a=a*(10**(t/20)/(np.sqrt((a**2).mean())+1e-9)); pk=np.abs(a).max(); return a*(0.89/pk) if pk>0.89 else a
N=load('au2/n.wav'); S=load('au2/s.wav'); H=load('au2/h.wav')
nq,_=cut(N,0,5.54,th=-60); nl,_=cut(N,5.55,len(N)/SR,th=-60)
s1,_=cut(S,0.0,5.21,th=-60); s2,_=cut(S,5.22,6.97,th=-60); gob,_=cut(S,6.98,8.2,th=-60,pad=0.04); s4,_=cut(S,8.22,13.1); sl,_=cut(S,13.1,len(S)/SR)
h1,_=cut(H,0.0,6.42,th=-60); h2,h2src=cut(H,6.43,10.70,th=-60); hl,_=cut(H,10.71,len(H)/SR,th=-60)
SB=load('au2/sB.wav'); HB=load('au2/hB.wav'); NB=load('au2/nB.wav')
reks,_=cut(SB,0.0,2.49,th=-60); s4n,_=cut(SB,2.5,8.15); tk1,_=cut(SB,8.19,9.23,th=-75,pad=0.02); ngg,_=cut(SB,9.26,11.60,th=-70,pad=0.02); tk2,_=cut(SB,11.66,len(SB)/SR,th=-70,pad=0.02)
sama,_=cut(HB,0.0,3.30,th=-60); kar,karsrc=cut(HB,3.31,7.04,th=-60); hati,hatisrc=cut(HB,7.05,len(HB)/SR,th=-60)
OM=load('au2/om.wav'); om,_=cut(OM,0.0,len(OM)/SR,th=-60,pad=0.03)
ciye,_=cut(NB,0.0,2.34,th=-60); emang,_=cut(NB,2.35,len(NB)/SR,th=-60)
def fade(a,d=0.08):
    a=a.copy(); n=int(d*SR); a[-n:]*=np.linspace(1,0,n); return a
HT=load('au2/htawa1.wav')
def seg(a,s0,e0,fo=0.7): x,_=cut(a,s0,min(e0+0.45,len(a)/SR),th=-60,pad=0.02); return fade(x,fo)
htA=seg(HT,0.05,1.5); htE=seg(HT,6.42,8.85); htF=seg(HT,8.92,10.85); htG=seg(HT,11.05,13.55,fo=1.2)
LN0=load('lz/N0.wav'); LN1=load('lz/N1.wav'); LH0=load('lz/H0.wav'); LH1=load('lz/H1.wav'); LH2=load('lz/H2.wav')
def sg(a,s0,e0,fo=0.22): x,_=cut(a,s0,min(e0,len(a)/SR),th=-60,pad=0.02); return fade(x,fo)
n0=sg(LN0,0.05,3.25,0.5); n0a=sg(LN0,0.05,1.6,0.35); n1a=sg(LN1,0.0,1.92); n1b=sg(LN1,1.97,2.95)
h0a=sg(LH0,0.05,1.03); h0b=sg(LH0,1.07,1.93); h0=sg(LH0,0.05,2.45,0.3); h1c=sg(LH1,0.15,0.85); h2a=sg(LH2,0.05,1.33); h2ab=sg(LH2,0.05,2.33,0.3); h2c=sg(LH2,2.37,4.15,0.4)
hls=fade(hl[:int(0.80*SR)]); hls2=fade(hl[:int(0.76*SR)],0.25); nls=fade(nl[:int(1.75*SR)],0.55); sl=fade(sl,0.35); hlong=np.concatenate([hls,hls[int(0.05*SR):]*0.8])
ev=[]; tracks={'N':[], 'S':[], 'H':[]}
def put(spk,a,t,kind='talk',gain=1.0,name=''):
    a=norm(a)*gain
    if spk=='N':
        from scipy.signal import butter,lfilter
        b_,a_=butter(2,3800/(SR/2)); a=lfilter(b_,a_,a).astype(np.float32)*0.42
    tracks[spk].append((int(t*SR),a)); d=len(a)/SR
    ev.append(dict(spk=spk,t0=t,t1=t+d,kind=kind,name=name)); return t+d
t=0.4
t=put('N',nq,t,name='q')
t=put('S',s1,t+0.10,name='s1')
t=put('H',h1,t+0.04,name='h1')
t=put('S',reks,t-0.05,name='reks')
t=put('H',sama,t+0.0,name='sama')
t=put('S',s2,t+0.05,name='s2')
h2t=t+0.10; h2e=put('H',h2,h2t,name='h2')
gt=h2t+(7.74-h2src); put('S',gob,gt,gain=1.15,name='gob')
ge_=gt+len(gob)/SR
put('S',sl,ge_-0.08,kind='laugh',gain=0.6,name='slg')
put('N',n0a,ge_+0.05,kind='laugh',gain=0.8,name='nlg')
put('H',h2a,h2e+0.02,kind='laugh',gain=0.55,name='hl')
s4e=put('S',s4n,h2e+0.55,name='s4')
kt=s4e-0.10; ke=put('H',kar,kt,name='kar')
ST=load('lz/ST0.wav'); p1=ST[int(0.06*SR):int(0.78*SR)].copy(); p2=ST[int(2.12*SR):int(3.42*SR)].copy()
xf=int(0.04*SR); p1[-xf:]*=np.linspace(1,0,xf); p2[:xf]*=np.linspace(0,1,xf)
pfft=fade(ST[int(2.10*SR):int(3.44*SR)].copy(),0.25)
put('S',pfft,kt+0.08,kind='laugh',gain=0.65,name='slk')
put('N',n0a,kt+0.40,kind='laugh',gain=0.8,name='nlk')
pass
t1=kt+(5.75-karsrc); t1e=put('S',tk1,t1,gain=1.1,name='tk1')
ome=put('S',om,t1e-0.04,name='om')
hle=put('H',h2c,ome-0.05,kind='laugh',gain=0.55,name='hlo')
ce=put('N',ciye,hle-0.75,name='ciye')
ee=put('N',emang,max(ce,hle)+0.02,name='emang')
ne=put('S',ngg,ee-0.30,gain=1.05,name='ngg')
ht=ne+0.02; hte=put('H',hati,ht,name='hati')
t2=ht+(9.15-hatisrc); se=put('S',tk2,t2,gain=1.05,name='tk2')
put('N',n0,hte+0.15,kind='laugh',gain=0.8,name='nl2')
put('H',h2ab,hte+0.02,kind='laugh',gain=0.55,name='hl2')
E_={e['name']:e for e in ev}
def R(spk,clip,t,gain,name): put(spk,clip,t,kind='laugh',gain=gain,name=name)
R('H',h0a,E_['s4']['t0']+1.3,0.4,'r7')                 # Herman ketawa di bawah omelan Sonya
R('H',h0a,E_['ngg']['t0']+0.9,0.45,'r12')
R('S',sl,E_['tk2']['t1']-0.15,0.6,'r14')               # tawa Sonya menyambung di penutup
se=max(e['t1'] for e in ev)-0.7
total=se+1.2
n=int(total*SR); mix=np.zeros(n,np.float32); envs={}
h=SR//FPS; nf=int(total*FPS)
for k,parts in tracks.items():
    tr=np.zeros(n+SR*3,np.float32)
    for i0,a in parts: tr[i0:i0+len(a)]+=a
    tr=tr[:n]; mix+=tr
    e=np.array([np.sqrt((tr[f*h:(f+1)*h]**2).mean()) for f in range(nf)])
    envs[k]=np.clip(e/0.09,0,1.5).tolist()
fo=int(0.8*SR); mix[-fo:]*=np.linspace(1,0,fo)
mix*=0.9/np.abs(mix).max()
wf.write('au2/mix.wav',SR,(mix*32767).astype(np.int16))
json.dump(dict(ev=ev,total=total,envs=envs),open('tl2.json','w'))
for k,parts in tracks.items():
    for (i0,a),e in zip(parts,[x for x in ev if x['spk']==k]): print(e['name'],k,round(e['t0'],2),round(e['t1'],2),'rms',round(20*np.log10(np.sqrt((a**2).mean())+1e-9)),'peak',round(20*np.log10(np.abs(a).max()+1e-9)))
print('total',round(total,2))
