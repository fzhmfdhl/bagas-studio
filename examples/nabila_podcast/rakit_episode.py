# Perakitan satu episode tanya-jawab (Nabila bertanya, Jers menjawab).
# Target: sekitar 60% motion, 40% talking.
import os,sys
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D=os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(D,'panggung.py')).read())
exec(open(os.path.join(D,'contoh_kartu.py')).read().split('\n\n',1)[1])   # CONTOH kartu; episode sungguhan merancang sendiri

# ---------- suara ----------
from toolkit.studio import voice_segments, word_times
QL=['Banyak yang nanya, AI ini bisa bantu apa sih buat usaha kecil?','Kenapa harus chat?','Terus caranya gimana?','Nggak takut nadanya jadi kaku?','Jadi kita tinggal apa?','Buat yang mau coba?']
AL=['Paling cepat kelihatan hasilnya di balas chat pelanggan.','Karena telat balas itu diam-diam makan omzet, dan jarang ada yang sadar.','Kumpulkan chat lama kamu, kasih ke AI, minta dia bikin draft balasan.','Nggak, karena contohnya dari chat kamu sendiri. Nada bicaranya tetap kamu.','Baca, benerin sedikit, kirim. Itu saja.','Tulis usaha kamu di komentar, nanti aku bedah satu.']
QS=voice_segments('q.wav',QL);AS=voice_segments('a.wav',AL)
AW=[word_times(AS[i]['audio'],AL[i]) for i in range(len(AL))]   # waktu tiap kata: pemicu ketukan & caption

# Pertanyaan pertama Nabila diputar DI ATAS kartu judul (cold open), bukan di shot Nabila.
LEAD=.45;GAP=.30;JHEAD=.70;TAIL=2.2
cues=[];t=LEAD
for i in range(6):
    q=QS[i]['audio'];a=AS[i]['audio']
    dq=len(q)/SR;da=len(a)/SR
    cues.append({'w':'N','a':t,'b':t+dq,'aud':q});t+=dq+GAP
    cues.append({'w':'J','a':t,'b':t+da,'aud':a,'card':i});t+=da+GAP
DUR=t-GAP+TAIL
print('total',round(DUR,2))
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
save_wav('ep7.wav',normalize(mix(normalize(voice,.92),music),.93))

def card_for(i,p,bg):
    if i==0:return c_statement(p,'MULAI DARI','Balas','chat','message-circle_ink')
    if i==1:return c_statement(p,'YANG DIAM-DIAM TERJADI','Order','hilang','trending-down_paper',dark=True)
    if i==2:return c_steps(p,'TIGA LANGKAH',[('inbox_ink','Kumpulkan chat lama'),('sparkles_ink','Minta AI buat draft'),('send_ink','Rapikan, lalu kirim')])
    if i==3:return c_two(p,'KENAPA NADANYA TETAP',('message-circle_ink','Contoh dari chatmu'),('user-round_ink','Nada tetap kamu'))
    if i==4:return c_three(p,'KAMU TINGGAL',['Baca','Benerin','Kirim'],['eye_ink','pencil_ink','send_ink'])
    return c_end(p,bg)

N=int(DUR*FPS);os.makedirs('f7',exist_ok=True)
def at(t):
    for c in cues:
        if c['a']-GAP/2<=t<c['b']+GAP/2:return c
    return None
mot=0
for fi in range(N):
    t=fi/FPS
    TOPEN=cues[0]['b']+GAP/2            # kartu judul menutupi seluruh pertanyaan pertama
    if t<TOPEN:
        im=c_title(min(1,t/max(.6,TOPEN*.55)),'AI buat usaha kecil','bisnis & AI  \u00b7  EP 00');mot+=1
    else:
        c=at(t)
        if c is None or (c['w']=='J' and t>cues[-1]['b']):
            im=c_end(1.0,shot_j(t,2));mot+=1
        elif c['w']=='N':
            p=(t-c['a'])/max(.01,c['b']-c['a'])
            k=int((t-c['a'])/.42)%2
            im=zoomed(shot_n(t,k),1.0+p*.03,int(p*-8))
        else:
            e=t-c['a'];p=e/max(.01,c['b']-c['a'])
            if e<JHEAD:
                k=int(e/.42)%2
                im=zoomed(shot_j(t,k),1.0+p*.035,int(p*-12))
            else:
                # progres mengikuti KATA yang sudah terdengar, bukan persentase durasi:
                # adegan baru lengkap saat kata terakhir mulai diucapkan, dan bertahan sampai suara habis.
                W=AW[c['card']];sudah=sum(1 for w in W if c['a']+w[1]<=t)
                im=card_for(c['card'],sudah/max(1,len(W)),shot_j(t,2));mot+=1
    px(im,2).save('f7/%04d.png'%fi)
print('frames',N,'motion',round(100*mot/N),'%')

# Cek sinkron (wajib): motion tidak boleh pergi sebelum suara selesai, ketukan terakhir dekat akhir jawaban.
for c in cues:
    if c['w']!='J':continue
    W=AW[c['card']];akhir_suara=c['a']+W[-1][2];akhir_motion=c['b']+GAP/2;ketukan=c['a']+W[-1][1]
    ok=akhir_motion>=akhir_suara and akhir_suara-ketukan<=1.0
    print('jawaban',c['card']+1,'suara',round(akhir_suara,2),'motion',round(akhir_motion,2),'ketukan_terakhir',round(ketukan,2),'OK' if ok else 'GAGAL')
