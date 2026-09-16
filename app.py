
import streamlit as st
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import random,math,io,time
import numpy as np
import pandas as pd

st.set_page_config(page_title="ORNAMENTAL GENOME AI",page_icon="🧬",layout="wide")
BASE=Path(__file__).parent; FILES=sorted((BASE/"assets"/"motifs").glob("master_*.png"))
NAMES=["Қошқар мүйіз","Қос мүйіз","Тұмарша","Төртқұлақ","Өрме мүйіз","Шеңбер өрнек","Бітпес","Қос ирек","Құсқанат"]
PALS={"Классика":["#bd322d","#f7eddb","#086176"],"Алтын дала":["#b68122","#f7e7c6","#175466"],
"Современный":["#0b6b77","#f8f0e2","#d43b32"],"Наурыз":["#116a53","#f5e6c7","#c18b22"]}
LAY=["Розетка","Бордюр","Квадратная","Центральная"]
st.markdown("""<style>
.stApp{background:linear-gradient(135deg,#052b3b,#0b5062);color:#fff}
.block-container{padding-top:1rem;max-width:1550px}
[data-testid=stSidebar]{background:#05293a}
[data-testid=stSidebar] *{color:#fff}
.hero{padding:22px 26px;border-radius:22px;background:linear-gradient(90deg,#0a4357,#0e6472);margin-bottom:14px}
.hero h1{margin:0;color:#fff}.hero p{color:#d9eaed}
.card{background:#fbf5e8;color:#0b3b4d;padding:18px;border-radius:20px;margin:12px 0}
div[data-testid=stButton] button{border-radius:12px;font-weight:800}
</style>""",unsafe_allow_html=True)
def rgb(h): h=h[1:]; return tuple(int(h[i:i+2],16) for i in (0,2,4))
def motif(i,color,size=180,mirror=False):
    im=Image.open(FILES[i]).convert("RGBA")
    if mirror: im=ImageOps.mirror(im)
    a=im.getchannel("A"); o=Image.new("RGBA",im.size,rgb(color)+(255,));o.putalpha(a)
    return o.resize((size,size),Image.LANCZOS)
def genome(mi,pal,lay):
    return {"motif":mi,"palette":pal,"layout":lay,"repeats":random.choice([4,6,8,10]),
    "scale":round(random.uniform(.55,.88),2),"rotation":random.choice([0,15,30,45,60,90]),
    "spacing":round(random.uniform(.82,1.12),2),"mirror":random.choice([0,1])}
def cross(a,b):
    c=dict(a)
    for k in ["repeats","scale","rotation","spacing","mirror","layout"]: c[k]=random.choice([a[k],b[k]])
    return c
def mutate(g,rate=.22):
    h=dict(g)
    if random.random()<rate:h["repeats"]=random.choice([4,6,8,10])
    if random.random()<rate:h["scale"]=round(float(np.clip(h["scale"]+random.uniform(-.08,.08),.48,.95)),2)
    if random.random()<rate:h["rotation"]=int(np.clip(h["rotation"]+random.choice([-15,15]),0,90))
    if random.random()<rate:h["mirror"]=1-h["mirror"]
    return h
def paste(base,im,x,y,sc,rot,mir=False):
    q=ImageOps.mirror(im) if mir else im;s=max(20,int(q.width*sc))
    q=q.resize((s,s),Image.LANCZOS).rotate(rot,expand=True,resample=Image.BICUBIC)
    base.paste(q,(int(x-q.width/2),int(y-q.height/2)),q)
def render(g,W=600,H=410):
    p=PALS[g["palette"]];b=Image.new("RGB",(W,H),rgb(p[1]));m=motif(g["motif"],p[0]);a=motif(g["motif"],p[2])
    n=g["repeats"];sc=g["scale"];r=g["rotation"]
    if g["layout"]=="Розетка":
        R=min(W,H)*.27*g["spacing"]
        for k in range(n):
            ang=2*math.pi*k/n;paste(b,m,W/2+R*math.cos(ang),H/2+R*math.sin(ang),sc*.72,math.degrees(ang)+r,bool(g["mirror"] and k%2))
        paste(b,a,W/2,H/2,sc*.55,r)
    elif g["layout"]=="Бордюр":
        for k in range(n):paste(b,m,(k+.5)*W/n,H/2,sc*.72,r if k%2==0 else -r,bool(g["mirror"] and k%2))
    elif g["layout"]=="Квадратная":
        for k,(x,y,rr) in enumerate([(W*.28,H*.28,0),(W*.72,H*.28,90),(W*.72,H*.72,180),(W*.28,H*.72,270)]):
            paste(b,m,x,y,sc*.85,rr+r,bool(g["mirror"] and k%2))
        paste(b,a,W/2,H/2,sc*.48,r)
    else: paste(b,m,W/2,H/2,sc*1.45,r)
    ImageDraw.Draw(b).rounded_rectangle((10,10,W-10,H-10),22,outline=rgb(p[2]),width=2)
    return b
def score(g): return float(np.clip(.83+.05*(g["repeats"]%2==0)-abs(g["scale"]-.72)*.12-abs(g["spacing"]-.96)*.08,0,.99))
def png(im):q=io.BytesIO();im.save(q,"PNG");return q.getvalue()
for k,v in {"pop":[],"gen":0,"sel":[],"final":None}.items():
    if k not in st.session_state:st.session_state[k]=v
with st.sidebar:
    st.markdown("## ◈ ORNAMENTAL<br>GENOME AI",unsafe_allow_html=True);st.caption("KAZAKH CREATIVE LAB")
    st.markdown("### ① Выберите мастер-мотив")
    mi=st.selectbox("Мотив",range(9),format_func=lambda i:NAMES[i],label_visibility="collapsed")
    st.image(motif(mi,"#c83a32",180),width=155);st.caption("Силуэт мотива не мутирует.")
    st.markdown("### ② Палитра и композиция")
    pal=st.selectbox("Палитра",list(PALS));lay=st.selectbox("Композиция",LAY)
    create=st.button("🚀 СОЗДАТЬ ПОКОЛЕНИЕ",use_container_width=True,type="primary")
st.markdown("""<div class=hero><b style="color:#f2bd58">НАСЛЕДИЕ → ГЕНОМ → ЭВОЛЮЦИЯ → ДИЗАЙН</b>
<h1>Эволюция казахского орнамента</h1><p>Мастер-мотив сохраняется. Эволюционируют только композиционные гены: повтор, масштаб, поворот, симметрия и расположение.</p></div>""",unsafe_allow_html=True)
tabs=st.tabs(["🎨 Дизайн-студия","🧬 Эволюция","🏛 Библиотека","👕 Применение","📊 Исследование"])
with tabs[0]:
    if create:
        bar=st.progress(0);ph=st.empty()
        for t,v in [("Считываем мастер-мотив",.2),("Кодируем Ornament DNA",.4),("Скрещиваем композиционные гены",.65),("Контролируем мутацию",.85),("Поколение готово",1)]:
            ph.markdown("### 🧬 "+t);bar.progress(v);time.sleep(.25)
        st.session_state.pop=[genome(mi,pal,lay) for _ in range(12)];st.session_state.gen=1;st.session_state.sel=[];st.rerun()
    st.markdown("<div class=card><h3>Как рождается новый дизайн</h3>",unsafe_allow_html=True)
    a=genome(mi,pal,lay);b=mutate(a,.8);c=mutate(cross(a,b),.3)
    cc=st.columns(3)
    for col,g,t in zip(cc,[a,b,c],["Родитель 1","Родитель 2","Потомок"]):
        with col:st.image(render(g,320,220),use_container_width=True);st.caption(t)
    st.markdown("</div>",unsafe_allow_html=True)
    if st.session_state.pop:
        st.markdown(f"<div class=card><h2>Поколение {st.session_state.gen} · 12 вариантов</h2>",unsafe_allow_html=True)
        cols=st.columns(6)
        for i,g in enumerate(st.session_state.pop):
            with cols[i%6]:
                st.image(render(g,330,230),use_container_width=True);st.caption(f"A{i+1:02d} · {score(g):.2f}")
                if st.button(("♥" if i in st.session_state.sel else "♡")+f" A{i+1:02d}",key=f"{st.session_state.gen}_{i}"):
                    if i in st.session_state.sel:st.session_state.sel.remove(i)
                    else:st.session_state.sel.append(i)
                    st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)
        x,y=st.columns(2)
        if x.button("🧬 Следующее поколение",use_container_width=True):
            ps=[st.session_state.pop[i] for i in st.session_state.sel]
            if len(ps)<2:st.warning("Выберите минимум 2 варианта.")
            else:
                bar=st.progress(0)
                for v in [.2,.45,.7,.9,1]:bar.progress(v);time.sleep(.28)
                st.session_state.pop=[mutate(cross(*random.sample(ps,2))) for _ in range(12)]
                st.session_state.gen+=1;st.session_state.sel=[];st.rerun()
        if y.button("🏆 Финальный вариант",use_container_width=True):
            pool=[st.session_state.pop[i] for i in st.session_state.sel] or st.session_state.pop
            st.session_state.final=max(pool,key=score)
    if st.session_state.final:
        g=st.session_state.final;im=render(g,1000,650)
        st.markdown("<div class=card><h2>🏆 Финальный дизайн</h2>",unsafe_allow_html=True)
        c1,c2=st.columns([1.4,.6])
        with c1:st.image(im,use_container_width=True)
        with c2:
            st.json({"Мастер-мотив":NAMES[g["motif"]],"Композиция":g["layout"],"Повторы":g["repeats"],"Масштаб":g["scale"],"Поворот":g["rotation"],"Fitness":round(score(g),3)})
            st.download_button("⬇ Скачать PNG",png(im),"ornamental_genome.png","image/png",use_container_width=True)
        st.markdown("</div>",unsafe_allow_html=True)
with tabs[1]:
    st.markdown("<div class=card><h2>🧬 Главное правило V6</h2><p><b>Мы не мутируем культурный мотив.</b> Алгоритм наследует и изменяет только композиционные параметры. Поэтому Қошқар мүйіз остаётся Қошқар мүйізом.</p></div>",unsafe_allow_html=True)
with tabs[2]:
    st.markdown("<div class=card><h2>🏛 Мастер-библиотека</h2>",unsafe_allow_html=True)
    cols=st.columns(5)
    for i,n in enumerate(NAMES):
        with cols[i%5]:st.image(motif(i,"#173f4b"),use_container_width=True);st.caption(n)
    st.warning("Перед конкурсом названия и происхождение каждого мотива нужно сверить по академическим/музейным источникам.")
    st.markdown("</div>",unsafe_allow_html=True)
with tabs[3]:
    st.markdown("<div class=card><h2>👕 Применение</h2><p>Финальный орнамент можно использовать для упаковки, постера, текстиля, сувенира и фирменного паттерна.</p>",unsafe_allow_html=True)
    if st.session_state.final:st.image(render(st.session_state.final,900,500),use_container_width=True)
    else:st.info("Сначала выберите финальный дизайн.")
    st.markdown("</div>",unsafe_allow_html=True)
with tabs[4]:
    st.markdown("<div class=card><h2>📊 GA vs Random</h2>",unsafe_allow_html=True)
    trials=st.slider("Независимых запусков",5,30,10)
    if st.button("▶ Провести эксперимент"):
        rows=[]
        for t in range(trials):
            rnd=max(score(genome(mi,pal,lay)) for _ in range(60))
            pop=[genome(mi,pal,lay) for _ in range(12)]
            for _ in range(4):
                ps=sorted(pop,key=score,reverse=True)[:4]
                pop=[mutate(cross(*random.sample(ps,2))) for _ in range(12)]
            rows.append({"Запуск":t+1,"GA":max(map(score,pop)),"Random":rnd})
        df=pd.DataFrame(rows);st.line_chart(df.set_index("Запуск"));st.dataframe(df,use_container_width=True,hide_index=True)
    st.markdown("</div>",unsafe_allow_html=True)
