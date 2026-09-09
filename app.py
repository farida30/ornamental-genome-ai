
import streamlit as st
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
import random, math, time

st.set_page_config(page_title="ORNAMENTAL GENOME AI 2.0", page_icon="🧬", layout="wide")

st.markdown("""
<style>
.block-container{max-width:1280px;padding-top:1.3rem}
.hero{padding:24px;border-radius:20px;border:1px solid #ddd;margin-bottom:18px}
.hero h1{margin:0 0 8px 0}
.badge{display:inline-block;border:1px solid #ccc;border-radius:999px;padding:4px 9px;margin-right:5px}
</style>
<div class="hero">
<h1>🧬 ORNAMENTAL GENOME AI 2.0</h1>
<p>Эволюционная лаборатория генеративного дизайна казахского орнамента</p>
<span class="badge">Creative Industry</span>
<span class="badge">Genetic Algorithm</span>
<span class="badge">Machine Learning</span>
</div>
""", unsafe_allow_html=True)

CATEGORIES = {
    "Зооморфные":["Қошқар мүйіз","Қос мүйіз","Түйетабан","Құстаңдай","Қазмойын"],
    "Растительные":["Гүл","Жапырақ"],
    "Геометрические":["Тұмарша","Ирек"],
    "Космогонические":["Жұлдыз","Шұғыла","Төртқұлақ","Бітпес"]
}
MOTIFS=[m for v in CATEGORIES.values() for m in v]
SYMS=["Линейная","Зеркальная","Центральная","Радиальная"]
LAYOUTS=["Бордюр","Розетка","Центральная","Сетчатая"]
GENES=["motif","scale","rotation","repeats","spacing","symmetry","radius","density","curvature","secondary","layout"]

def clamp(x,a,b): return max(a,min(b,x))
def rot(x,y,a):
    a=np.deg2rad(a); return x*np.cos(a)-y*np.sin(a), x*np.sin(a)+y*np.cos(a)

def genome(motif=None):
    return dict(
        motif=MOTIFS.index(motif) if motif in MOTIFS else random.randrange(len(MOTIFS)),
        scale=random.uniform(.55,1.25), rotation=random.uniform(0,360),
        repeats=random.randint(4,18), spacing=random.uniform(.65,1.6),
        symmetry=random.randrange(4), radius=random.uniform(1.5,4),
        density=random.uniform(.45,.95), curvature=random.uniform(.6,1.35),
        secondary=random.uniform(0,.6), layout=random.randrange(4)
    )

def repair(g):
    g=dict(g)
    g["motif"]=int(clamp(round(g["motif"]),0,len(MOTIFS)-1))
    g["scale"]=clamp(float(g["scale"]),.35,1.55)
    g["rotation"]=float(g["rotation"])%360
    g["repeats"]=int(clamp(round(g["repeats"]),3,24))
    g["spacing"]=clamp(float(g["spacing"]),.45,2.1)
    g["symmetry"]=int(clamp(round(g["symmetry"]),0,3))
    g["radius"]=clamp(float(g["radius"]),1,5)
    g["density"]=clamp(float(g["density"]),.25,1)
    g["curvature"]=clamp(float(g["curvature"]),.35,1.65)
    g["secondary"]=clamp(float(g["secondary"]),0,.9)
    g["layout"]=int(clamp(round(g["layout"]),0,3))
    return g

def motif_paths(name,s=1,c=1):
    p=[]
    if name=="Қошқар мүйіз":
        t=np.linspace(0,2.3*np.pi,150); r=s*(.04+.105*t*c)
        x=r*np.cos(t); y=r*np.sin(t); p=[(x,y),(-x,y)]
    elif name=="Қос мүйіз":
        t=np.linspace(0,2*np.pi,130); r=s*(.04+.09*t*c)
        x=r*np.cos(t); y=r*np.sin(t); p=[(x-.25*s,y),(-x+.25*s,y)]
    elif name=="Түйетабан":
        x=np.array([-.65,-.25,0,.25,.65,.35,0,-.35,-.65])*s
        y=np.array([0,.45,.18,.45,0,-.4,-.12,-.4,0])*s; p=[(x,y)]
    elif name=="Құстаңдай":
        x=np.array([-.8,-.25,0,.25,.8,.35,0,-.35,-.8])*s
        y=np.array([0,.2,.65,.2,0,-.18,-.5,-.18,0])*s; p=[(x,y)]
    elif name=="Қазмойын":
        t=np.linspace(-np.pi/2,1.3*np.pi,130)
        p=[(.45*s*np.cos(t)+.18*s*np.sin(2*t)*c,.62*s*np.sin(t))]
    elif name=="Гүл":
        t=np.linspace(0,2*np.pi,220); r=s*(.48+.22*np.cos(6*t)); p=[(r*np.cos(t),r*np.sin(t))]
    elif name=="Жапырақ":
        t=np.linspace(0,np.pi,120); x=s*np.cos(t); y=.48*s*np.sin(t)
        p=[(x,y),(x,-y),(np.array([-s,s]),np.array([0,0]))]
    elif name=="Тұмарша":
        p=[(np.array([0,.72,-.72,0])*s,np.array([.78,-.58,-.58,.78])*s),
           (np.array([0,.28,-.28,0])*s,np.array([.28,-.22,-.22,.28])*s)]
    elif name=="Ирек":
        x=np.linspace(-1,1,160)*s; y=.32*s*np.sin(3*np.pi*x/max(s,.01)); p=[(x,y)]
    elif name=="Жұлдыз":
        pts=[]
        for i in range(16):
            rr=s*(.85 if i%2==0 else .34); a=np.pi*i/8; pts.append((rr*np.cos(a),rr*np.sin(a)))
        pts.append(pts[0]); p=[(np.array([q[0] for q in pts]),np.array([q[1] for q in pts]))]
    elif name=="Шұғыла":
        for i in range(12):
            a=2*np.pi*i/12; p.append((np.array([.18,.9])*s*np.cos(a),np.array([.18,.9])*s*np.sin(a)))
    elif name=="Төртқұлақ":
        for a in [0,90,180,270]:
            t=np.linspace(0,1.7*np.pi,90); r=s*(.05+.1*t)
            x,y=rot(r*np.cos(t)+.22*s,r*np.sin(t),a); p.append((x,y))
    else:
        t=np.linspace(-1,1,180); x=s*t; y=.33*s*np.sin(2.5*np.pi*t); p=[(x,y),(x,-y)]
    return p

def draw_one(ax,name,x,y,a,s,c,mirror=False,lw=1.8):
    for px,py in motif_paths(name,s,c):
        if mirror: px=-px
        xx,yy=rot(np.array(px),np.array(py),a)
        ax.plot(xx+x,yy+y,linewidth=lw)

def draw(g,title=None):
    g=repair(g); fig,ax=plt.subplots(figsize=(6,6))
    name=MOTIFS[g["motif"]]; n=g["repeats"]; r=g["radius"]; s=g["scale"]; lay=LAYOUTS[g["layout"]]
    if lay=="Бордюр":
        for i,x in enumerate(np.linspace(-r,r,n)):
            draw_one(ax,name,x,0,g["rotation"]+(i%2)*180,s*.58,g["curvature"],i%2==1)
    elif lay=="Розетка":
        for i in range(n):
            th=2*np.pi*i/n; rr=r*(.62+.25*g["density"])
            draw_one(ax,name,rr*np.cos(th),rr*np.sin(th),g["rotation"]+np.degrees(th),s*.64,g["curvature"])
    elif lay=="Центральная":
        m=max(4,n//2)
        for i in range(m):
            th=2*np.pi*i/m; rr=r*.72
            draw_one(ax,name,rr*np.cos(th),rr*np.sin(th),g["rotation"]+np.degrees(th),s*.62,g["curvature"])
        draw_one(ax,name,0,0,g["rotation"],s,g["curvature"])
    else:
        side=max(2,min(5,int(round(math.sqrt(n)))))
        for iy,y in enumerate(np.linspace(-r*.7,r*.7,side)):
            for ix,x in enumerate(np.linspace(-r*.7,r*.7,side)):
                draw_one(ax,name,x,y,g["rotation"]+(ix+iy)*45,s*.46,g["curvature"],(ix+iy)%2==1,1.4)
    lim=r+1.6; ax.set(xlim=(-lim,lim),ylim=(-lim,lim)); ax.set_aspect("equal"); ax.axis("off")
    if title: ax.set_title(title)
    return fig

def scores(g):
    g=repair(g)
    sym=.95 if (g["symmetry"] in [2,3] and g["repeats"]%2==0) else .78
    fill=(g["repeats"]*g["scale"]*g["density"])/(12*.85)
    comp=float(np.exp(-1.2*abs(fill-1))*np.exp(-.4*abs(g["spacing"]-1.05)))
    tradition=float(np.exp(-.9*abs(g["curvature"]-1))*np.exp(-.5*max(0,g["scale"]-1.3)))
    novelty=clamp(.55*min(abs(g["curvature"]-1)/.55,1)+.25*min((g["rotation"]%90)/45,1)+.2*g["secondary"],0,1)
    crowd=(g["scale"]*g["density"]*g["repeats"])/max(g["spacing"],.3)
    clean=clamp(1-max(0,crowd-9)/18,0,1)
    return dict(symmetry=sym,composition=comp,tradition=tradition,novelty=novelty,clean=clean)

def feat(g): return np.array([g[k] for k in GENES],float)

if "labels" not in st.session_state: st.session_state.labels=[]
if "trainset" not in st.session_state: st.session_state.trainset=[]

def train_model():
    if len(st.session_state.labels)<8: return None
    X=np.vstack([feat(x["g"]) for x in st.session_state.labels]); y=np.array([x["target"] for x in st.session_state.labels])
    if np.std(y)<.02: return None
    m=RandomForestRegressor(n_estimators=180,random_state=42)
    m.fit(X,y); return m

model=train_model()

with st.sidebar:
    st.header("⚙️ Эксперимент")
    cat=st.selectbox("Категория",list(CATEGORIES))
    motif=st.selectbox("Мотив",CATEGORIES[cat])
    pop=st.slider("Популяция",20,140,60,10)
    gens=st.slider("Поколения",5,80,35,5)
    mut=st.slider("Мутация",.01,.35,.10,.01)
    aiw=st.slider("Вес AI‑эксперта",0.,.6,.25,.05)

weights={"symmetry":.20,"composition":.25,"tradition":.30,"novelty":.15,"clean":.10}

def fitness(g):
    ms=scores(g); base=sum(weights[k]*ms[k] for k in weights); ai=None
    if model is not None:
        ai=float(clamp(model.predict(feat(g).reshape(1,-1))[0],0,1))
        base=(1-aiw)*base+aiw*ai
    return float(base),ms,ai

def cross(a,b):
    c={}
    for k in GENES:
        if k in ["motif","repeats","symmetry","layout"]: c[k]=a[k] if random.random()<.5 else b[k]
        else:
            q=random.random(); c[k]=q*a[k]+(1-q)*b[k]
    return repair(c)

def mutate(g,p):
    g=dict(g)
    for k in GENES:
        if k=="motif": continue
        if random.random()<p:
            if k=="repeats": g[k]+=random.choice([-2,-1,1,2])
            elif k=="symmetry": g[k]=random.randrange(4)
            elif k=="layout": g[k]=random.randrange(4)
            elif k=="rotation": g[k]+=random.uniform(-40,40)
            else: g[k]+=random.uniform(-.2,.2)
    return repair(g)

def evolve():
    P=[genome(motif) for _ in range(pop)]; hist=[]; snaps=[]
    for gen in range(gens+1):
        sc=np.array([fitness(g)[0] for g in P]); order=np.argsort(sc)[::-1]
        hist.append([gen,float(sc.max()),float(sc.mean())])
        if gen in sorted(set([0,gens//2,gens])): snaps.append((gen,dict(P[order[0]]),float(sc.max())))
        if gen==gens: break
        new=[dict(P[i]) for i in order[:max(2,pop//10)]]
        while len(new)<pop:
            ids=random.sample(range(pop),min(3,pop)); p1=P[max(ids,key=lambda i:sc[i])]
            ids=random.sample(range(pop),min(3,pop)); p2=P[max(ids,key=lambda i:sc[i])]
            new.append(mutate(cross(p1,p2),mut))
        P=new[:pop]
    sc=[fitness(g)[0] for g in P]; i=int(np.argmax(sc))
    return P[i],pd.DataFrame(hist,columns=["generation","best","mean"]),snaps,P,sc

tabs=st.tabs(["🎨 Студия","🧬 Эволюция","🤖 Обучение ИИ","📊 Исследование","📚 О проекте"])

with tabs[0]:
    st.header("Студия")
    st.write("Теперь используются 13 отдельных параметрических мотивов, а не три условные фигуры.")
    c1,c2,c3=st.columns(3)
    with c1:
        m=st.selectbox("Мотив",MOTIFS,index=MOTIFS.index(motif),key="s_m")
        scale=st.slider("Масштаб",.35,1.55,.8,.05)
        curve=st.slider("Изгиб / пластика",.35,1.65,1.,.05)
    with c2:
        rep=st.slider("Повторы",3,24,8)
        rotv=st.slider("Поворот",0,359,0)
        dens=st.slider("Плотность",.25,1.,.7,.05)
    with c3:
        lay=st.selectbox("Композиция",LAYOUTS,index=1)
        sym=st.selectbox("Симметрия",SYMS,index=3)
        rad=st.slider("Радиус",1.,5.,2.8,.1)
    g=genome(m); g.update(scale=scale,curvature=curve,repeats=rep,rotation=rotv,density=dens,layout=LAYOUTS.index(lay),symmetry=SYMS.index(sym),radius=rad)
    sc,ms,ai=fitness(g)
    a,b=st.columns([1.2,1])
    with a:
        fig=draw(g,f"{m} • {lay} • Fitness {sc:.3f}"); st.pyplot(fig,use_container_width=True); plt.close(fig)
    with b:
        st.dataframe(pd.DataFrame({"Критерий":list(ms),"Оценка":list(ms.values())}),hide_index=True,use_container_width=True)
        if ai is None: st.info("AI‑эксперт пока не обучен.")
        else: st.metric("AI‑эксперт",f"{ai*100:.1f}%")

with tabs[1]:
    st.header("Эволюция")
    if st.button("🚀 Запустить эволюцию",type="primary"):
        t=time.time(); best,hist,snaps,P,sc=evolve()
        st.session_state.run=(best,hist,snaps,P,sc,time.time()-t)
    if "run" in st.session_state:
        best,hist,snaps,P,sc,elapsed=st.session_state.run
        a,b=st.columns([1.2,1])
        with a:
            fig=draw(best,f"Победитель • Fitness {fitness(best)[0]:.3f}"); st.pyplot(fig,use_container_width=True); plt.close(fig)
        with b:
            st.metric("Время",f"{elapsed:.2f} сек")
            st.dataframe(pd.DataFrame({"Ген":GENES,"Значение":[best[k] for k in GENES]}),hide_index=True,use_container_width=True)
        st.subheader("Поколения")
        cols=st.columns(len(snaps))
        for c,(gn,gg,ss) in zip(cols,snaps):
            with c:
                fig=draw(gg,f"Поколение {gn}\n{ss:.3f}"); st.pyplot(fig,use_container_width=True); plt.close(fig)
        st.line_chart(hist.set_index("generation")[["best","mean"]])

with tabs[2]:
    st.header("Как обучается ИИ")
    st.markdown("""
**1.** Сайт генерирует примеры → **2.** человек оценивает их →
**3.** формируется таблица «11 генов → экспертная оценка» →
**4.** обучается `RandomForestRegressor` →
**5.** прогноз модели добавляется к Fitness следующего поколения.
""")
    st.metric("Размеченных примеров",len(st.session_state.labels))
    if model is None: st.warning("Нужно минимум 8 разнообразно оценённых вариантов.")
    else: st.success("AI‑эксперт обучен и участвует в Fitness.")
    if st.button("Создать 8 вариантов для разметки"):
        st.session_state.trainset=[genome(motif) for _ in range(8)]
    for i,gc in enumerate(st.session_state.trainset):
        with st.expander(f"Вариант {i+1}",expanded=i==0):
            l,r=st.columns([1,1])
            with l:
                fig=draw(gc); st.pyplot(fig,use_container_width=True); plt.close(fig)
            with r:
                s=st.slider("Сохранение характера мотива",1,5,3,key=f"q_s{i}")
                h=st.slider("Гармония",1,5,3,key=f"q_h{i}")
                o=st.slider("Оригинальность",1,5,3,key=f"q_o{i}")
                if st.button("Сохранить оценку",key=f"q_b{i}"):
                    target=(.45*s+.35*h+.20*o)/5
                    st.session_state.labels.append({"g":dict(gc),"target":target,"style":s,"harmony":h,"originality":o})
                    st.success("Добавлено.")
    if st.session_state.labels:
        rows=[]
        for x in st.session_state.labels:
            row={k:x["g"][k] for k in GENES}; row.update(target=x["target"],style=x["style"],harmony=x["harmony"],originality=x["originality"]); rows.append(row)
        df=pd.DataFrame(rows); st.dataframe(df,use_container_width=True)
        st.download_button("Скачать обучающую выборку CSV",df.to_csv(index=False).encode("utf-8-sig"),"ornamental_ai_training.csv","text/csv")

with tabs[3]:
    st.header("Сравнение случайной и эволюционной генерации")
    if st.button("🧪 Провести эксперимент"):
        R=[genome(motif) for _ in range(pop)]; rs=[fitness(g)[0] for g in R]
        best,hist,snaps,P,es=evolve()
        res=pd.DataFrame({
            "Метод":["Случайная","Эволюционная"],
            "Средний Fitness":[np.mean(rs),np.mean(es)],
            "Лучший Fitness":[np.max(rs),np.max(es)],
            "Популяция":[pop,pop],"Поколения":[0,gens],"Мотив":[motif,motif]
        })
        st.session_state.res=res
    if "res" in st.session_state:
        st.dataframe(st.session_state.res,hide_index=True,use_container_width=True)
        st.bar_chart(st.session_state.res.set_index("Метод")[["Средний Fitness","Лучший Fitness"]])
        st.download_button("Скачать результаты CSV",st.session_state.res.to_csv(index=False).encode("utf-8-sig"),"experiment_results.csv","text/csv")

with tabs[4]:
    st.header("Научная логика")
    st.write("""
**Библиотека:** 13 мотивов в 4 категориях.  
**Геном:** 11 параметров.  
**Эволюция:** отбор, скрещивание, мутация, элитизм.  
**ИИ:** Random Forest обучается на экспертной разметке пользователя.  
**Честное ограничение:** контуры являются авторскими стилизованными параметрическими моделями для вычислительного эксперимента, а не точными музейными копиями.
""")
    table=[]
    for c,ms in CATEGORIES.items():
        for m in ms: table.append({"Категория":c,"Мотив":m})
    st.dataframe(pd.DataFrame(table),hide_index=True,use_container_width=True)
