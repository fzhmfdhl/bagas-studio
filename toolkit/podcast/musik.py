import numpy as np, wave, scipy.io.wavfile as wf
from scipy.signal import butter, lfilter
SR=44100
w=wave.open('ep3/mix.wav'); vo=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
N=len(vo); T=N/SR
rng=np.random.default_rng(7)
BPM=92; beat=60/BPM; bar=beat*4
def midi(m): return 440*2**((m-69)/12)
def ep(f,d,vel=1.0):     # piano elektrik lembut
    n=int(d*SR); t=np.arange(n)/SR
    env=np.exp(-t*2.2)*(1-np.exp(-t*80))
    x=np.sin(2*np.pi*f*t)+0.35*np.sin(2*np.pi*2*f*t)*np.exp(-t*4)+0.12*np.sin(2*np.pi*3*f*t)*np.exp(-t*6)
    trem=1+0.06*np.sin(2*np.pi*4.5*t)
    return x*env*trem*vel
def lp(x,fc):
    b,a=butter(2,fc/(SR/2)); return lfilter(b,a,x)
out=np.zeros(N+SR*4,np.float32)
def put(x,t0):
    i=int(t0*SR)
    if i>=len(out): return
    j=min(len(out),i+len(x)); out[i:j]+=x[:j-i]
# progresi: Fmaj7 - Em7 - Dm7 - Cmaj7 (santai, hangat)
CH=[[53,57,60,64],[52,55,59,62],[50,53,57,60],[48,52,55,59]]
BASS=[41,40,38,36]
t=0.0; k=0
while t<T+bar:
    ch=CH[k%4]
    for j,m in enumerate(ch):                    # akor sedikit digeser (strum)
        put(ep(midi(m),bar*1.1,0.16),t+j*0.025)
    put(ep(midi(ch[-1]+12),beat*1.5,0.07),t+beat*2.5)   # nada hias
    nb=int(bar*SR); tb=np.arange(nb)/SR
    put(0.22*np.sin(2*np.pi*midi(BASS[k%4])*tb)*np.exp(-tb*0.9)*(1-np.exp(-tb*40)),t)
    for b in range(4):                           # kick lembut + hi-hat
        if b in (0,2):
            n=int(0.25*SR); tt=np.arange(n)/SR; f=55+70*np.exp(-tt*30)
            put(0.28*np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*14),t+b*beat)
        if b in (1,3):
            n=int(0.12*SR); put(lp(rng.standard_normal(n),3500)*0.05*np.exp(-np.arange(n)/SR*25),t+b*beat)
        for h in (0.5,):
            n=int(0.05*SR); x=rng.standard_normal(n); x=x-lp(x,6000)
            put(x*0.025*np.exp(-np.arange(n)/SR*60),t+b*beat+h*beat)
    t+=bar; k+=1
m=out[:N]
m=lp(m,5200)
# derak vinil tipis
cr=np.zeros(N,np.float32); idx=rng.integers(0,N,int(T*9)); cr[idx]=rng.uniform(-0.3,0.3,len(idx))
m+=lp(cr,4000)*0.15+lp(rng.standard_normal(N),900)*0.004
# fade
fi=int(1.5*SR); fo=int(3.0*SR); m[:fi]*=np.linspace(0,1,fi); m[-fo:]*=np.linspace(1,0,fo)
m/=np.abs(m).max()+1e-9
# ducking mengikuti suara
h=int(0.02*SR); e=np.array([np.sqrt((vo[i:i+h]**2).mean()) for i in range(0,N,h)])
g=np.where(e>0.02,0.35,1.0); g=np.repeat(g,h)[:N]
g=lfilter([1-0.9995],[1,-0.9995],g)            # transisi halus
m*=g*0.13
mix=vo+m; mix/=max(1,np.abs(mix).max()/0.95)
wf.write('ep3/mix_musik.wav',SR,(mix*32767).astype(np.int16))
print('ok',T)
