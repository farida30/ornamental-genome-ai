
import streamlit as st
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import numpy as np, pandas as pd, random, math, io, time

st.set_page_config(page_title="ORNAMENTAL GENOME AI", page_icon="🧬", layout="wide", initial_sidebar_state="expanded")
BASE=Path(__file__).parent
FILES=sorted((BASE/"assets"/"motifs").glob("master_*.png"))

NAMES=["Қошқар мүйіз","Қос мүйіз","Тұмарша","Төртқұлақ","Өрме мүйіз","Шеңбер өрнек","Бітпес","Қос ирек","Құсқанат"]
STRUCTURES=["Розетка","Медальон","Квадрат","Бордюр","Сетка","Зеркальная пара"]
SYMM=["2-лучевая","4-лучевая","6-лучевая","8-лучевая"]
LINKS=["сцепленное","касательное","свободное","вложенное"]
RHYTHMS=["равномерный","чередующийся","нарастающий"]
PALS={
 "Классика":["#C8322D","#F8EEDD","#0A6172","#D9A43A"],
 "Бирюза и золото":["#0B6A76","#F7EAD0","#C38A24","#C73530"],
 "Красный этно":["#B92D29","#F8EBD7","#8B1F20","#D6A03A"],
 "Современный":["#0A5064","#F7F0E4","#D33B31","#0C766A"]
}

st.markdown("""
<style>
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important}
#MainMenu,footer{visibility:hidden}
.stApp{background:radial-gradient(circle at 70% 0,#135b6b 0,#073849 43%,#052b3b 100%);color:#f8f1e5}
.block-container{padding:.8rem 1.2rem 3rem;max-width:1600px}
[data-testid="stSidebar"]{background:#052a3a;border-right:1px solid rgba(255,255,255,.08)}
[data-testid="stSidebar"] label,[data-testid="stSidebar"] p,[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{color:#f8f1e5!important}
[data-baseweb="select"]>div{background:#fff!important;color:#173b48!important}
[data-baseweb="select"] span{color:#173b48!important}
[data-baseweb="popover"] *{color:#173b48!important}
.hero{padding:22px 27px;border-radius:22px;background:linear-gradient(105deg,#0a4357,#106c78);box-shadow:0 15px 40px rgba(0,0,0,.2);margin-bottom:14px}
.hero h1{margin:.2rem 0;color:#fff;font-size:2.3rem}.hero p{color:#dcebed;margin:.3rem 0}
.cream{background:#fbf5e8;color:#0a3b4c;border-radius:22px;padding:18px 20px;box-shadow:0 15px 35px rgba(0,0,0,.18);margin:14px 0}
.dna{background:#eef0e5;border-left:5px solid #e4ad42;padding:12px;border-radius:13px;color:#153e49}
div[data-testid="stButton"] button,div[data-testid="stDownloadButton"] button{border-radius:13px;font-weight:800}
</style>
""",unsafe_allow_html=True)

def rgb(h): h=h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))
def master(i,color,size=220,mirror=False):
    im=Image.open(FILES[i]).convert("RGBA")
    if mirror: im=ImageOps.mirror(im)
    a=im.getchannel("A")
    out=Image.new("RGBA",im.size,rgb(color)+(255,)); out.putalpha(a)
    return out.resize((size,size),Image.LANCZOS)

def put(base,im,x,y,scale=1,rot=0,mirror=False):
    q=ImageOps.mirror(im) if mirror else im
    s=max(28,int(q.width*scale))
    q=q.resize((s,s),Image.LANCZOS).rotate(rot,expand=True,resample=Image.BICUBIC)
    base.paste(q,(int(x-q.width/2),int(y-q.height/2)),q)

def ray_count(sym): return int(sym.split("-")[0])

def new_genome(mi,pal,structure=None):
    structure=structure or random.choice(STRUCTURES)
    return {
      "motif":mi, "palette":pal, "structure":structure,
      "symmetry":random.choice(SYMM),
      "link":random.choice(LINKS),
      "rhythm":random.choice(RHYTHMS),
      "count":random.choice([4,6,8,10,12]),
      "scale":round(random.uniform(.72,1.12),2),
      "density":round(random.uniform(.62,.92),2),
      "rotation":random.choice([0,15,30,45]),
      "mirror":random.choice([0,1]),
      "secondary":random.choice([0,1]),
      "secondary_motif":random.choice([x for x in range(len(NAMES)) if x!=mi]),
    }

def crossover(a,b):
    c={"motif":a["motif"],"palette":random.choice([a["palette"],b["palette"]])}
    # Real chromosome crossover: inherit composition genes from either parent.
    for k in ["structure","symmetry","link","rhythm","count","scale","density","rotation","mirror","secondary","secondary_motif"]:
        c[k]=random.choice([a[k],b[k]])
    return c

def mutate(g,rate=.24):
    h=dict(g); changed=[]
    choices={
      "structure":STRUCTURES,"symmetry":SYMM,"link":LINKS,"rhythm":RHYTHMS,
      "count":[4,6,8,10,12],"rotation":[0,15,30,45],"mirror":[0,1]
    }
    for k,vals in choices.items():
        if random.random()<rate:
            old=h[k]; h[k]=random.choice(vals)
            if h[k]!=old: changed.append(k)
    if random.random()<rate:
        h["scale"]=round(float(np.clip(h["scale"]+random.uniform(-.16,.16),.62,1.18)),2); changed.append("scale")
    if random.random()<rate:
        h["density"]=round(float(np.clip(h["density"]+random.uniform(-.12,.12),.5,.96)),2); changed.append("density")
    h["_mutations"]=changed
    return h

def render(g,W=640,H=440):
    p=PALS[g["palette"]]; bg=Image.new("RGB",(W,H),rgb(p[1]))
    m=master(g["motif"],p[0],220); alt=master(g["secondary_motif"],p[2],190)
    sc=g["scale"]; den=g["density"]; rot=g["rotation"]; n=g["count"]; stc=g["structure"]
    gap={"сцепленное":.76,"касательное":.9,"свободное":1.12,"вложенное":.68}[g["link"]]
    # Large, dense compositions; master silhouette stays intact.
    if stc=="Розетка":
        rays=ray_count(g["symmetry"]); R=min(W,H)*(.20+.11*(1-den))*gap
        for k in range(rays):
            a=2*math.pi*k/rays
            put(bg,m,W/2+R*math.cos(a),H/2+R*math.sin(a),sc*.88,math.degrees(a)+rot,bool(g["mirror"] and k%2))
        if g["secondary"]: put(bg,alt,W/2,H/2,sc*.78,rot)
    elif stc=="Медальон":
        rays=max(4,ray_count(g["symmetry"])); R=min(W,H)*.23*gap
        for k in range(rays):
            a=2*math.pi*k/rays
            put(bg,m,W/2+R*math.cos(a),H/2+R*math.sin(a),sc*.82,math.degrees(a)+90+rot,bool(k%2))
        put(bg,m,W/2,H/2,sc*1.05,rot,bool(g["mirror"]))
    elif stc=="Квадрат":
        pts=[(W*.28,H*.27,0),(W*.72,H*.27,90),(W*.72,H*.73,180),(W*.28,H*.73,270)]
        for k,(x,y,r) in enumerate(pts): put(bg,m,x,y,sc*.95,r+rot,bool(g["mirror"] and k%2))
        if g["secondary"]: put(bg,alt,W/2,H/2,sc*.88,45+rot)
    elif stc=="Бордюр":
        nn=max(5,min(10,n)); step=W/(nn+.4)
        for k in range(nn):
            yy=H/2 + (28 if g["rhythm"]=="чередующийся" and k%2 else -10)
            ss=sc*(.72 + (.035*k if g["rhythm"]=="нарастающий" else 0))
            put(bg,m,(k+.7)*step,yy,ss,rot if k%2==0 else -rot,bool(g["mirror"] and k%2))
    elif stc=="Сетка":
        cols=4; rows=3
        for r in range(rows):
            for c in range(cols):
                ss=sc*.67
                rr=rot+(180 if (r+c)%2 else 0)
                put(bg,m,(c+.5)*W/cols,(r+.5)*H/rows,ss,rr,bool(g["mirror"] and (r+c)%2))
    else: # mirrored pair / emblem
        put(bg,m,W*.38,H/2,sc*1.35,-rot,False)
        put(bg,m,W*.62,H/2,sc*1.35,rot,True)
        if g["secondary"]: put(bg,alt,W/2,H/2,sc*.62,90)
    d=ImageDraw.Draw(bg); d.rounded_rectangle((10,10,W-10,H-10),22,outline=rgb(p[3]),width=3)
    return bg

def fitness(g):
    # Transparent heuristic, not "beauty truth".
    symmetry=1.0 if g["symmetry"] in ["4-лучевая","6-лучевая","8-лучевая"] else .82
    density=1-abs(g["density"]-.78)
    structure=.94 if g["structure"] in ["Розетка","Медальон","Квадрат"] else .88
    diversity=.86 + .08*g["secondary"] + .04*(g["link"]=="сцепленное")
    return float(np.clip(.30*symmetry+.28*density+.24*structure+.18*diversity,0,.99))

def png(im):
    b=io.BytesIO(); im.save(b,"PNG"); return b.getvalue()

# Safe state initialization + migration away from old V6/V7 keys.
defaults={"population":[],"generation":0,"selected":[],"final_design":None,"history":[],"likes":[]}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k]=v
if not isinstance(st.session_state["population"],list): st.session_state["population"]=[]

with st.sidebar:
    st.markdown("## ◈ ORNAMENTAL<br>GENOME AI",unsafe_allow_html=True); st.caption("KAZAKH CREATIVE LAB")
    st.markdown("### ① Мастер-мотив")
    mi=st.selectbox("Мотив",range(len(NAMES)),format_func=lambda i:NAMES[i],label_visibility="collapsed")
    st.image(master(mi,"#C93430",190),width=165)
    st.caption("Культурный силуэт сохраняется.")
    st.markdown("### ② Палитра")
    pal=st.selectbox("Палитра",list(PALS),label_visibility="collapsed")
    st.markdown("### ③ Тип стартовой композиции")
    start_structure=st.selectbox("Структура",["Автоматически"]+STRUCTURES,label_visibility="collapsed")
    create=st.button("🚀 СОЗДАТЬ ПОКОЛЕНИЕ",use_container_width=True,type="primary")

st.markdown("""<div class="hero"><b style="color:#f0bd58">НАСЛЕДИЕ → ГЕНОМ → ЭВОЛЮЦИЯ → ИИ → ДИЗАЙН</b>
<h1>Эволюция казахского орнамента</h1>
<p>Новый дизайн рождается не из поворота одной картинки: алгоритм скрещивает структуру, симметрию, ритм, плотность, способ соединения и другие гены целой композиции.</p></div>""",unsafe_allow_html=True)

tabs=st.tabs(["🎨 Дизайн-студия","🧬 Скрещивание","🏛 Библиотека","✨ ИИ-профиль","👕 Применение","📊 Исследование"])

with tabs[0]:
    if create:
        ph=st.empty(); bar=st.progress(0)
        for txt,v in [("Считываем мастер-мотив",.15),("Создаём 11-генный Ornament DNA",.33),("Формируем разные архитектуры",.55),("Проверяем симметрию и плотность",.75),("Создаём 12 потомков",1)]:
            ph.markdown("### 🧬 "+txt); bar.progress(v); time.sleep(.22)
        forced=None if start_structure=="Автоматически" else start_structure
        pop=[]
        # guarantee structural diversity in the first generation
        structs=STRUCTURES*2
        random.shuffle(structs)
        for i in range(12):
            pop.append(new_genome(mi,pal,forced or structs[i]))
        st.session_state["population"]=pop
        st.session_state["generation"]=1
        st.session_state["selected"]=[]
        st.session_state["final_design"]=None
        st.rerun()

    if not st.session_state["population"]:
        st.markdown('<div class="cream"><h2>Начните с мастер-мотива</h2><p>Слева выберите мотив и нажмите «Создать поколение». Первое поколение специально содержит разные архитектуры, а не один рисунок под разными углами.</p></div>',unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="cream"><h2>Поколение {st.session_state["generation"]} · 12 разных композиций</h2>',unsafe_allow_html=True)
        cols=st.columns(4)
        for i,g in enumerate(st.session_state["population"]):
            with cols[i%4]:
                st.image(render(g,470,330),use_container_width=True)
                st.markdown(f"**A{i+1:02d} · {g['structure']}**")
                st.caption(f"{g['symmetry']} · {g['link']} · Fitness {fitness(g):.2f}")
                chosen=i in st.session_state["selected"]
                if st.button(("♥ Выбрано" if chosen else "♡ Выбрать"),key=f"pick_{st.session_state['generation']}_{i}",use_container_width=True):
                    if chosen: st.session_state["selected"].remove(i)
                    else: st.session_state["selected"].append(i)
                    st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)
        c1,c2=st.columns(2)
        if c1.button("🧬 СКРЕСТИТЬ ВЫБРАННЫЕ",use_container_width=True):
            parents=[st.session_state["population"][i] for i in st.session_state["selected"]]
            if len(parents)<2: st.warning("Выберите минимум 2 композиции-родителя.")
            else:
                st.session_state["history"].append(parents[:])
                ph=st.empty(); bar=st.progress(0)
                for txt,v in [("Отбор родителей",.18),("Crossover: наследование генов",.42),("Mutation: изменение отдельных признаков",.66),("Проверка мастер-мотива",.84),("12 новых потомков готовы",1)]:
                    ph.markdown("### "+txt); bar.progress(v); time.sleep(.3)
                children=[]
                while len(children)<12:
                    a,b=random.sample(parents,2)
                    children.append(mutate(crossover(a,b),.25))
                st.session_state["population"]=children
                st.session_state["generation"]+=1
                st.session_state["selected"]=[]
                st.rerun()
        if c2.button("🏆 ВЫБРАТЬ ФИНАЛЬНЫЙ",use_container_width=True):
            pool=[st.session_state["population"][i] for i in st.session_state["selected"]] or st.session_state["population"]
            st.session_state["final_design"]=max(pool,key=fitness)

        if st.session_state["final_design"]:
            g=st.session_state["final_design"]; im=render(g,1000,700)
            st.markdown('<div class="cream"><h2>🏆 Финальный дизайн</h2>',unsafe_allow_html=True)
            a,b=st.columns([1.35,.65])
            with a: st.image(im,use_container_width=True)
            with b:
                st.markdown("### Ornament DNA")
                st.json({"Мотив":NAMES[g["motif"]],"Структура":g["structure"],"Симметрия":g["symmetry"],"Соединение":g["link"],"Ритм":g["rhythm"],"Элементов":g["count"],"Масштаб":g["scale"],"Плотность":g["density"],"Поворот":g["rotation"],"Зеркальность":bool(g["mirror"]),"Вторичный мотив":NAMES[g["secondary_motif"]] if g["secondary"] else "нет"})
                st.download_button("⬇ Скачать PNG",png(im),"ornamental_genome_v8.png","image/png",use_container_width=True)
            st.markdown("</div>",unsafe_allow_html=True)

with tabs[1]:
    st.markdown('<div class="cream"><h2>🧬 Что именно наследует потомок?</h2>',unsafe_allow_html=True)
    if st.session_state["history"]:
        parents=st.session_state["history"][-1]
        if len(parents)>=2:
            a,b=parents[0],parents[1]; child=mutate(crossover(a,b),.3)
            c1,c2,c3=st.columns(3)
            for col,g,title in [(c1,a,"Родитель A"),(c2,b,"Родитель B"),(c3,child,"Потомок")]:
                with col: st.image(render(g,420,300),use_container_width=True); st.markdown(f"**{title}: {g['structure']}**")
            st.markdown(f"""<div class="dna"><b>Пример генома потомка:</b><br>
            структура = {child['structure']} · симметрия = {child['symmetry']} · соединение = {child['link']} ·
            ритм = {child['rhythm']} · масштаб = {child['scale']} · плотность = {child['density']}<br>
            <b>Мутации:</b> {", ".join(child.get("_mutations",[])) or "нет"}
            </div>""",unsafe_allow_html=True)
    else: st.info("В Дизайн-студии выберите минимум два варианта и нажмите «Скрестить выбранные».")
    st.markdown("</div>",unsafe_allow_html=True)

with tabs[2]:
    st.markdown('<div class="cream"><h2>🏛 Мастер-библиотека</h2><p>Базовый силуэт не мутирует. Алгоритм строит из него новые композиционные структуры.</p>',unsafe_allow_html=True)
    cols=st.columns(5)
    for i,n in enumerate(NAMES):
        with cols[i%5]: st.image(master(i,"#173F4B",210),use_container_width=True); st.markdown(f"**{n}**")
    st.warning("Названия и культурную атрибуцию каждого мастер-мотива перед финальной защитой необходимо сверить по академическим/музейным источникам.")
    st.markdown("</div>",unsafe_allow_html=True)

with tabs[3]:
    st.markdown('<div class="cream"><h2>✨ Персональный ИИ-профиль</h2>',unsafe_allow_html=True)
    st.write("ИИ здесь не заменяет эволюционный алгоритм. Его задача — учиться на выборе пользователя и затем ранжировать композиции по персональному вкусу.")
    st.markdown("**Пользователь выбирает → сохраняются гены выбранных дизайнов → модель изучает закономерности → следующие поколения получают AI Match.**")
    st.info("В V8 этот раздел показывает корректную архитектуру ИИ. Постоянное обучение между сеансами потребует облачной базы пользователей (например, Supabase).")
    st.markdown("</div>",unsafe_allow_html=True)

with tabs[4]:
    st.markdown('<div class="cream"><h2>👕 От орнамента к графическому продукту</h2>',unsafe_allow_html=True)
    if st.session_state["final_design"]:
        st.image(render(st.session_state["final_design"],1000,520),use_container_width=True)
        st.write("Финальную композицию можно использовать как основу для упаковки, текстиля, постера, сувенира, фирменного паттерна или публикации в социальных сетях.")
    else: st.info("Сначала выберите финальный дизайн.")
    st.markdown("</div>",unsafe_allow_html=True)

with tabs[5]:
    st.markdown('<div class="cream"><h2>📊 Исследование: эволюционный поиск vs случайная генерация</h2>',unsafe_allow_html=True)
    trials=st.slider("Независимых запусков",5,30,10)
    if st.button("▶ Провести эксперимент"):
        rows=[]
        for t in range(trials):
            # Equal budget: 60 evaluated candidates each.
            rnd=[new_genome(mi,pal) for _ in range(60)]
            random_best=max(map(fitness,rnd))
            pop=[new_genome(mi,pal) for _ in range(12)]
            evaluated=12
            while evaluated<60:
                parents=sorted(pop,key=fitness,reverse=True)[:4]
                pop=[mutate(crossover(*random.sample(parents,2)),.25) for _ in range(12)]
                evaluated+=12
            ga_best=max(map(fitness,pop))
            rows.append({"Запуск":t+1,"GA":ga_best,"Random":random_best})
        df=pd.DataFrame(rows)
        st.line_chart(df.set_index("Запуск")); st.dataframe(df,use_container_width=True,hide_index=True)
        st.metric("Средняя разница GA − Random",f"{(df.GA-df.Random).mean():+.3f}")
        st.download_button("⬇ Скачать CSV",df.to_csv(index=False).encode("utf-8-sig"),"v8_ga_vs_random.csv","text/csv")
    st.caption("Fitness — прозрачная техническая эвристика структуры/симметрии/плотности, а не утверждение об объективной красоте орнамента.")
    st.markdown("</div>",unsafe_allow_html=True)
