# CONTOH kartu motion dari episode pertama JERSTALK.
# INI BUKAN TEMPLATE. Jangan dipakai ulang mentah-mentah; tiap episode merancang tampilannya sendiri.
# Yang boleh ditiru dari sini: cara memakai lay()/draw_stack()/_wipe()/fit()/cek_kartu(), bukan rupanya.
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'panggung.py')).read(),'panggung.py','exec'))

# 1. pembuka -----------------------------------------------------------------
def c_title(p,title,sub,brand='JERSTALK',ic='mic'):
    im=paper();L=Image.new('RGBA',(W,H),(0,0,0,0));d0=ImageDraw.Draw(L)
    f,lines=fit(d0,title,RGT-LFT,150,74,maxlines=3)
    fb=F('Bold',58)
    it=[(190,lambda L,y,a,dx,ic=ic:icon(L,ic,CX+dx,y+95,180,a)),
        (72,lambda L,y,a,dx:ctext(ImageDraw.Draw(L),y,brand,fb,A(INK,a),cx=CX+dx)),
        (22,lambda L,y,a,dx:rule(ImageDraw.Draw(L),y,a,160,cx=CX+dx)),
        (len(lines)*(f.size+16),lambda L,y,a,dx:[ctext(ImageDraw.Draw(L),y+i*(f.size+16),l,f,A(INK,a),cx=CX+dx) for i,l in enumerate(lines)]),
        (54,lambda L,y,a,dx:ctext(ImageDraw.Draw(L),y,sub,F('Medium',38),A(MUTE,a),cx=CX+dx))]
    draw_stack(L,it,p,gap=34)
    return _done(im,L)

# 2. dua kata raksasa --------------------------------------------------------
def c_statement(p,eyebrow,w1,w2,ic=None,dark=False):
    im=paper(INK if dark else PAPER);L=Image.new('RGBA',(W,H),(0,0,0,0));d0=ImageDraw.Draw(L)
    fg=PAPER if dark else INK
    f1,_=fit(d0,w1,RGT-LFT,215,110,maxlines=1);f2,_=fit(d0,w2,RGT-LFT,215,110,maxlines=1)
    fS=F('Bold',min(f1.size,f2.size))
    it=[]
    if ic:it.append((176,lambda L,y,a,dx,ic=ic:icon(L,ic,CX+dx,y+88,164,a)))
    it+=[(50,lambda L,y,a,dx:lab(ImageDraw.Draw(L),y,eyebrow,a,cx=CX+dx)),
         (int(fS.size*1.18),lambda L,y,a,dx:ctext(ImageDraw.Draw(L),y,w1,fS,A(fg,a),cx=CX+dx)),
         (int(fS.size*1.18),lambda L,y,a,dx:ctext(ImageDraw.Draw(L),y,w2,fS,A(ACC,a),cx=CX+dx)),
         (22,lambda L,y,a,dx:rule(ImageDraw.Draw(L),y,a,120,cx=CX+dx))]
    draw_stack(L,it,p,gap=26,entr='left',st=.13)
    return _done(im,L)

# 3. blok warna penuh --------------------------------------------------------
def c_block(p,eyebrow,kalimat,ic=None,col=None):
    col=col or ACC
    im=paper();L=Image.new('RGBA',(W,H),(0,0,0,0))
    _wipe(L,(0,0,W,H),p*1.9,'down',col)
    q=max(0,(p-.34)/.66)
    if q>0:
        d0=ImageDraw.Draw(L)
        f,lines=fit(d0,kalimat,RGT-LFT,124,62,maxlines=4)
        it=[]
        if ic:it.append((168,lambda L,y,a,dx,ic=ic:icon(L,ic,CX+dx,y+84,156,a)))
        it+=[(50,lambda L,y,a,dx:lab(ImageDraw.Draw(L),y,eyebrow,a,cx=CX+dx,col=(255,228,218))),
             (len(lines)*(f.size+14),lambda L,y,a,dx:[ctext(ImageDraw.Draw(L),y+i*(f.size+14),l,f,A(PAPER,a),cx=CX+dx) for i,l in enumerate(lines)])]
        draw_stack(L,it,q,gap=36)
    return _done(im,L)

# 4. daftar langkah ----------------------------------------------------------
def c_steps(p,eyebrow,rows,nomor=True):
    im=paper();L=Image.new('RGBA',(W,H),(0,0,0,0));d0=ImageDraw.Draw(L)
    n=max(1,len(rows));rh=min(190,max(120,(BOT-TOP-200)//n))
    f=F('Bold',min(66,max(44,int(rh*.40))))
    def mkrow(i,ic,t):
        def fn(L,y,a,dx):
            d=ImageDraw.Draw(L);x=LFT+dx
            if nomor:
                d.text((x,y+rh//2-30),'%02d'%(i+1),font=F('Bold',44),fill=A(ACC,a));x+=104
            if ic:icon(L,ic,x+44,y+rh//2,86,a);d=ImageDraw.Draw(L);x+=118
            for j,l in enumerate(wrap(d,t,f,RGT-x+LFT-dx)[:2]):
                d.text((x,y+rh//2-f.size//2-6+j*(f.size+4)),l,font=f,fill=A(INK,a))
            d.rectangle([LFT+dx,y+rh-6,LFT+dx+int((RGT-LFT)*a),y+rh-3],fill=A(LINE,a))
        return fn
    it=[(50,lambda L,y,a,dx:lab(ImageDraw.Draw(L),y,eyebrow,a,cx=CX+dx)),
        (22,lambda L,y,a,dx:rule(ImageDraw.Draw(L),y,a,120,cx=CX+dx))]
    for i,r in enumerate(rows):
        ic,t=(r if isinstance(r,(list,tuple)) else (None,r))
        it.append((rh,mkrow(i,ic,t)))
    draw_stack(L,it,p,gap=18,entr='left',st=.12)
    return _done(im,L)

# 5. layar terbelah ----------------------------------------------------------
def c_two(p,eyebrow,kiri,kanan,ket=''):
    im=paper();L=Image.new('RGBA',(W,H),(0,0,0,0))
    _wipe(L,(CX,0,W,H),p*2.2,'left',INK)
    d=ImageDraw.Draw(L);d.rectangle([0,0,W,16],fill=A(ACC,1))
    q=max(0,(p-.3)/.7);a0=ease(q*4)
    if a0>0:
        d.rectangle([CX-2,0,CX+2,H],fill=A(LINE,a0*.55))   # penuh, supaya tidak jadi isi setengah kolom
        if eyebrow:lab(d,TOP+8,eyebrow,a0,col=MUTE)
        for i,(side,col) in enumerate([(kiri,INK),(kanan,PAPER)]):
            ic,t=(side if isinstance(side,(list,tuple)) else (None,side))
            a=ease((q-i*.12)*4.5);dy=int((1-a)*26)
            if a<=0:continue
            cx=CX//2 if i==0 else CX+CX//2
            d0=ImageDraw.Draw(L);f,lines=fit(d0,t,CX-120,96,48,maxlines=2)
            blk=200+34+len(lines)*(f.size+10)
            y0=MIDY-blk//2+dy
            if ic:icon(L,ic,cx,y0+100,190,a)
            d=ImageDraw.Draw(L);yy=y0+234
            for l in lines:ctext(d,yy,l,f,A(col,a),cx=cx);yy+=f.size+10
        if ket:
            a2=ease((q-.5)*4)
            d.ellipse([CX-58,MIDY-58,CX+58,MIDY+58],fill=A(ACC,a2))
            ctext(d,MIDY-36,ket,F('Bold',58),A(PAPER,a2))
    return _done(im,L)

# 6. tiga pita ---------------------------------------------------------------
def c_three(p,eyebrow,words,icons=None):
    im=paper();L=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(L)
    a0=ease(p*4.5)
    if eyebrow:lab(d,TOP-4,eyebrow,a0)
    n=max(1,len(words));top=TOP+86;hgt=(BOT-top)//n
    for i,wd in enumerate(words):
        a=ease((p-.12-i*.17)*4.5)
        if a<=0:continue
        y=top+i*hgt
        bg=[PAPER,(235,232,226),INK][i%3] if n==3 else (PAPER if i%2==0 else INK)
        fgc=PAPER if bg==INK else INK
        _wipe(L,(0,y,W,y+hgt-12),min(1,a*1.35),'right' if i%2==0 else 'left',bg)
        d=ImageDraw.Draw(L);f,_=fit(d,wd,RGT-LFT-210,100,50,maxlines=1)
        cx=CX
        if icons and i<len(icons) and icons[i]:
            icon(L,icons[i],LFT+96,y+hgt//2-6,100,a);d=ImageDraw.Draw(L);cx=CX+76
        ctext(d,y+hgt//2-f.size//2-6,wd,f,A(fgc,a),cx=cx)
        d.text((RGT-54,y+hgt//2-28),str(i+1),font=F('Bold',42),fill=A(ACC,a))
    return _done(im,L)

# 7. kutipan -----------------------------------------------------------------
def c_quote(p,kalimat,sumber=''):
    im=paper(INK);L=Image.new('RGBA',(W,H),(0,0,0,0));d0=ImageDraw.Draw(L)
    f,lines=fit(d0,kalimat,RGT-LFT,116,58,maxlines=5)
    def qm(L,y,a,dx):
        d=ImageDraw.Draw(L)
        for k in range(2):
            x=LFT+dx+k*46
            d.polygon([(x,y),(x+34,y),(x+20,y+56),(x,y+56)],fill=A(ACC,a))
    it=[(60,qm),
        (len(lines)*(f.size+14),lambda L,y,a,dx:[ImageDraw.Draw(L).text((LFT+dx,y+i*(f.size+14)),l,font=f,fill=A(PAPER,a)) for i,l in enumerate(lines)])]
    if sumber:
        it.append((58,lambda L,y,a,dx:(rule(ImageDraw.Draw(L),y,a,90,cx=LFT+45+dx),ImageDraw.Draw(L).text((LFT+dx,y+20),sumber,font=F('Medium',38),fill=A(MUTE,a)))))
    draw_stack(L,it,p,gap=38)
    return _done(im,L)

# 8. lencana -----------------------------------------------------------------
def c_badge(p,kata,ket='',ic=None):
    im=paper(INK);L=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(L)
    a=ease(p*5.5);dy=int((1-a)*18)
    rr=364;cy=MIDY-60+dy
    d.ellipse([CX-rr,cy-rr,CX+rr,cy+rr],outline=A(ACC,a),width=10)
    d.ellipse([CX-rr+34,cy-rr+34,CX+rr-34,cy+rr-34],outline=A(ACC,a*.45),width=4)
    d0=ImageDraw.Draw(L);f,lines=fit(d0,kata,2*rr-190,170,80,maxlines=2)
    inner=[]
    if ic:inner.append((150,lambda L,y,aa,dx,ic=ic:icon(L,ic,CX,y+75,140,aa)))
    inner.append((len(lines)*(f.size+10),lambda L,y,aa,dx:[ctext(ImageDraw.Draw(L),y+i*(f.size+10),l,f,A(PAPER,aa)) for i,l in enumerate(lines)]))
    draw_stack(L,inner,p,top=cy-rr+70,bot=cy+rr-70,gap=26,st=.08)
    if ket:
        a2=ease((p-.45)*4);ctext(ImageDraw.Draw(L),cy+rr+54,ket,F('Medium',42),A(MUTE,a2))
    return _done(im,L)

# 9. lakukan / jangan --------------------------------------------------------
def c_check(p,eyebrow,baik,buruk):
    im=paper();L=Image.new('RGBA',(W,H),(0,0,0,0))
    items=[(x,True) for x in baik]+[(x,False) for x in buruk]
    n=max(1,len(items));rh=min(190,max(124,(BOT-TOP-190)//n))
    f=F('Bold',min(60,max(42,int(rh*.38))))
    def mk(t,ok):
        def fn(L,y,a,dx):
            d=ImageDraw.Draw(L);_mark(d,LFT+46+dx,y+rh//2,46,ok,a)
            for j,l in enumerate(wrap(d,t,f,RGT-LFT-160)[:2]):
                d.text((LFT+140+dx,y+rh//2-f.size//2-6+j*(f.size+4)),l,font=f,fill=A(INK,a))
        return fn
    it=[(50,lambda L,y,a,dx:lab(ImageDraw.Draw(L),y,eyebrow,a,cx=CX+dx)),
        (22,lambda L,y,a,dx:rule(ImageDraw.Draw(L),y,a,120,cx=CX+dx))]
    it+=[(rh,mk(t,ok)) for t,ok in items]
    draw_stack(L,it,p,gap=16,entr='alt',st=.11)
    return _done(im,L)

# 10. penutup (latar bersih, tanpa wajah) ------------------------------------
def c_end(p,bg=None,ajakan='Tulis usahamu di komentar',ket='nanti aku bedah satu',akun='@jerapahmerah_',ic='message-circle'):
    im=paper();L=Image.new('RGBA',(W,H),(0,0,0,0));d0=ImageDraw.Draw(L)
    f,lines=fit(d0,ajakan,RGT-LFT,128,66,maxlines=3)
    fw=F('Bold',46);wq,_=tw(d0,akun,fw)
    it=[(196,lambda L,y,a,dx,ic=ic:icon(L,ic,CX+dx,y+98,184,a)),
        (len(lines)*(f.size+14),lambda L,y,a,dx:[ctext(ImageDraw.Draw(L),y+i*(f.size+14),l,f,A(INK,a),cx=CX+dx) for i,l in enumerate(lines)]),
        (22,lambda L,y,a,dx:rule(ImageDraw.Draw(L),y,a,120,cx=CX+dx)),
        (56,lambda L,y,a,dx:ctext(ImageDraw.Draw(L),y,ket,F('Medium',42),A(MUTE,a),cx=CX+dx)),
        (92,lambda L,y,a,dx:(ImageDraw.Draw(L).rounded_rectangle([CX-wq//2-40+dx,y,CX+wq//2+40+dx,y+88],30,outline=A(ACC,a),width=5),ctext(ImageDraw.Draw(L),y+20,akun,fw,A(ACC,a),cx=CX+dx)))]
    draw_stack(L,it,p,gap=30,st=.09)
    return _done(im,L)

KARTU={'c_title':c_title,'c_statement':c_statement,'c_block':c_block,'c_steps':c_steps,
       'c_two':c_two,'c_three':c_three,'c_quote':c_quote,'c_badge':c_badge,
       'c_check':c_check,'c_end':c_end}

