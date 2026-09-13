import streamlit as st
from pathlib import Path
from PIL import Image
import numpy as np, random, math, io, time

st.set_page_config(page_title='ORNAMENTAL GENOME AI', page_icon='🧬', layout='wide', initial_sidebar_state='expanded')
BASE=Path(__file__).parent
MOTIF_DIR=BASE/'assets'/'motifs'
FILES=sorted(MOTIF_DIR.glob('motif_*.png'))
NAMES=['Мүйіз I','Қошқар мүйіз','Мүйіз өрнек','Төрт мүйіз','Гүл өрнек','Қос мүйіз','Тұмарша','Бордюр мүйіз','Төртқұлақ I','Өрме мүйіз','Шеңбер өрнек','Төртқұлақ II','Бітпес','Қос ирек','Қанат мүйіз','Қос өрнек','Өрім','Төртқұлақ III','Шеңбер мүйіз','Құсқанат','Ирек мүйіз']
PALETTES={'Классика':['#C8322D','#F2E9D5','#0C5368'],'Современный':['#0D6875','#E5AA36','#F5EEE0'],'Минимал':['#102F3B','#F4EBDD','#B7792D'],'Наурыз':['#11755D','#D9A62E','#F4E6C8'],'Контраст':['#C92F2C','#0A4F63','#E6B34D']}
PRODUCTS=['Упаковка','Постер','Текстиль','Сувенир','Соцсети','Логотип-паттерн']
LAYOUTS=['Розетка','Бордюр','Сетка','Центр']

st.markdown('''<style>
.stApp{background:linear-gradient(180deg,#062d40 0,#0c4758 100%);color:#f7f1e5}.block-container{padding:.8rem 1.3rem 2rem;max-width:1600px}
[data-testid="stSidebar"]{background:#052b3c;border-right:1px solid rgba(255,255,255,.08)}[data-testid="stSidebar"] *{color:#f8f1e5}
.og-top{background:linear-gradient(90deg,rgba(6,47,66,.96),rgba(15,79,93,.92));border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:18px 24px;margin-bottom:14px}.og-title{font-size:2.15rem;font-weight:900;color:#fff}.og-sub{color:#d6e5e9}
.cream{background:#fbf6ea;border-radius:22px;padding:18px;color:#09384a;box-shadow:0 16px 38px rgba(0,0,0,.18);margin-bottom:14px}.step{display:inline-block;width:26px;height:26px;border-radius:50%;background:#14bbd1;color:#fff;text-align:center;line-height:26px;font-weight:900;margin-right:8px}
div[data-testid="stButton"] button{border-radius:13px;font-weight:800}.hero-btn div[data-testid="stButton"] button{background:linear-gradient(90deg,#edb94f,#ffd77f);color:#173847;border:none;min-height:48px;font-weight:900}
</style>''',unsafe_allow_html=True)

def rgb(h):
    h=h.lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))

def motif(i,color,size=180):
    im=Image.open(FILES[i]).convert('RGBA'); a=im.getchannel('A')
    out=Image.new('RGBA',im.size,rgb(color)+(0,)); out.putalpha(a)
    c=Image.new('RGBA',(size,size),(0,0,0,0)); out.thumbnail((size-12,size-12),Image.LANCZOS); c.alpha_composite(out,((size-out.width)//2,(size-out.height)//2)); return c

def new_genome(mi,pal,lay):
    return {'motif_idx':mi,'palette':pal,'layout':lay,'repeats':random.randint(4,10),'scale':round(random.uniform(.62,1.05),2),'rotation':random.choice([0,15,30,45,60,90]),'spacing':round(random.uniform(.78,1.12),2),'seed':random.randint(1,999999)}

def mutate(g):
    h=dict(g); h['repeats']=int(np.clip(h['repeats']+random.choice([-2,-1,0,1,2]),3,12)); h['scale']=round(float(np.clip(h['scale']+random.uniform(-.12,.12),.5,1.18)),2); h['rotation']=int(np.clip(h['rotation']+random.choice([-15,0,15]),0,90)); h['spacing']=round(float(np.clip(h['spacing']+random.uniform(-.09,.09),.65,1.25)),2); return h

def cross(a,b):
    h=dict(a)
    for k in ['repeats','scale','rotation','spacing','layout']: h[k]=random.choice([a[k],b[k]])
    return mutate(h)

def score(g):
    structure=.82+.12*(g['repeats']%2==0)-abs(g['scale']-.82)*.10; balance=1-min(abs(g['spacing']-.95),.4); novelty=.55+.35*(g['rotation']/90); return max(0,min(.99,.48*structure+.32*balance+.20*novelty))

def compose(g,W=620,H=420):
    pal=PALETTES[g['palette']]; bg=Image.new('RGB',(W,H),rgb(pal[1])); m=motif(g['motif_idx'],pal[0],150); a=motif(g['motif_idx'],pal[2],150)
    def paste(im,x,y,s=1,r=0):
        q=im.resize((max(12,int(im.width*s)),max(12,int(im.height*s))),Image.LANCZOS).rotate(r,expand=True,resample=Image.BICUBIC); bg.paste(q,(int(x-q.width/2),int(y-q.height/2)),q)
    n=g['repeats']; lay=g['layout']
    if lay=='Розетка':
        R=min(W,H)*.29*g['spacing']
        for k in range(n):
            ang=2*math.pi*k/n; paste(m,W/2+R*math.cos(ang),H/2+R*math.sin(ang),g['scale'],math.degrees(ang)+g['rotation'])
        paste(a,W/2,H/2,g['scale']*.7,g['rotation'])
    elif lay=='Бордюр':
        for k in range(n): paste(m,(k+.5)*W/n,H/2,g['scale']*.78,g['rotation']*(1 if k%2==0 else -1))
    elif lay=='Сетка':
        cols=max(2,int(math.ceil(math.sqrt(n*1.4)))); rows=max(2,int(math.ceil(n/cols))); k=0
        for r in range(rows):
            for c in range(cols):
                if k>=n: break
                paste(m,(c+.5)*W/cols,(r+.5)*H/rows,g['scale']*.64,g['rotation']+(180 if (r+c)%2 else 0)); k+=1
    else:
        paste(m,W/2,H/2,g['scale']*1.85,g['rotation'])
        for k in range(max(4,n//2)):
            ang=2*math.pi*k/max(4,n//2); paste(a,W/2+W*.32*math.cos(ang),H/2+H*.32*math.sin(ang),g['scale']*.45,math.degrees(ang))
    return bg

def png(im):
    b=io.BytesIO(); im.save(b,format='PNG'); return b.getvalue()

for k,v in {'population':[],'generation':0,'picked':[],'final':None}.items():
    if k not in st.session_state: st.session_state[k]=v

with st.sidebar:
    st.markdown('## ◈ ORNAMENTAL\n### GENOME AI'); st.caption('KAZAKH CREATIVE LAB'); st.markdown('---')
    st.markdown("### <span class='step'>1</span> Выберите мотив",unsafe_allow_html=True)
    mi=st.selectbox('Мотив',range(len(NAMES)),format_func=lambda i:NAMES[i],label_visibility='collapsed'); st.image(motif(mi,'#D33A32',170),width=145); st.caption(NAMES[mi])
    st.markdown("### <span class='step'>2</span> Выберите продукт",unsafe_allow_html=True); product=st.selectbox('Продукт',PRODUCTS,label_visibility='collapsed')
    st.markdown("### <span class='step'>3</span> Стиль и палитра",unsafe_allow_html=True); pal=st.radio('Палитра',list(PALETTES),horizontal=True,label_visibility='collapsed'); lay=st.selectbox('Композиция',LAYOUTS)
    st.markdown('<div class="hero-btn">',unsafe_allow_html=True); create=st.button('🚀 СОЗДАТЬ ПОКОЛЕНИЕ',use_container_width=True); st.markdown('</div>',unsafe_allow_html=True)

st.markdown('''<div class="og-top"><div style="font-size:.78rem;font-weight:900;letter-spacing:.16em;color:#e9b957">ТРАДИЦИЯ × ТЕХНОЛОГИИ × ТВОРЧЕСТВО</div><div class="og-title">Эволюция казахского орнамента</div><div class="og-sub">Выберите традиционный мотив → получите поколение современных композиций → отберите лучшие → создайте новый дизайн.</div></div>''',unsafe_allow_html=True)

tabs=st.tabs(['🎨 Дизайн-студия','🧬 Эволюция','🏛 Библиотека','📁 Мои дизайны','✨ ИИ-профиль','📊 Исследование'])
with tabs[0]:
    if create:
        bar=st.progress(0,'Читаем признаки мотива...')
        for i,t in enumerate(['Кодируем Ornament DNA','Формируем популяцию','Применяем вариации','Проверяем композиции','Готово']): bar.progress((i+1)/5,t); time.sleep(.18)
        st.session_state.population=[new_genome(mi,pal,lay) for _ in range(12)]; st.session_state.generation=1; st.session_state.picked=[]; st.session_state.final=None; st.rerun()
    st.markdown('<div class="cream">',unsafe_allow_html=True); st.markdown('### Как рождается новый дизайн')
    p1=new_genome(mi,pal,lay); p2=mutate(p1); ch=cross(p1,p2); c1,c2,c3=st.columns(3)
    with c1: st.image(compose(p1,280,180),use_container_width=True); st.caption('Родитель 1')
    with c2: st.image(compose(p2,280,180),use_container_width=True); st.caption('Родитель 2')
    with c3: st.image(compose(ch,280,180),use_container_width=True); st.caption('Скрещивание + мутация → новый дизайн')
    st.markdown('</div>',unsafe_allow_html=True)
    if not st.session_state.population: st.info('Слева выберите мотив, продукт, палитру и нажмите «СОЗДАТЬ ПОКОЛЕНИЕ».')
    else:
        st.markdown(f'<div class="cream"><h3>Поколение {st.session_state.generation} · 12 вариантов</h3>',unsafe_allow_html=True); cols=st.columns(6)
        for i,g in enumerate(st.session_state.population):
            with cols[i%6]:
                st.image(compose(g,330,230),use_container_width=True); st.caption(f'A{i+1:02d} · {score(g):.2f}'); on=i in st.session_state.picked
                if st.button(('♥ ' if on else '♡ ')+f'A{i+1:02d}',key=f'pk_{st.session_state.generation}_{i}',use_container_width=True):
                    if on: st.session_state.picked.remove(i)
                    else: st.session_state.picked.append(i)
                    st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)
        a,b,c=st.columns(3)
        if a.button('🧬 Следующее поколение',use_container_width=True):
            sel=[st.session_state.population[i] for i in st.session_state.picked]
            if len(sel)<2: st.warning('Выберите минимум два понравившихся варианта.')
            else:
                ph=st.empty(); bar=st.progress(0)
                for text,p in [('Отбор родителей',.18),('Скрещивание генов',.42),('Мутация',.68),('Проверка композиции',.87),('Новое поколение готово',1.0)]: ph.markdown(f'### {text}'); bar.progress(p); time.sleep(.3)
                st.session_state.population=[cross(*random.sample(sel,2)) for _ in range(12)]; st.session_state.generation+=1; st.session_state.picked=[]; st.rerun()
        if b.button('🏆 Выбрать лучший',use_container_width=True): st.session_state.final=max(st.session_state.population,key=score)
        if c.button('🎲 Новая серия',use_container_width=True): st.session_state.population=[new_genome(mi,pal,lay) for _ in range(12)]; st.session_state.picked=[]; st.rerun()
        if st.session_state.final:
            fg=st.session_state.final; st.markdown('<div class="cream">',unsafe_allow_html=True); st.markdown('## 🏆 Финальный дизайн'); x,y=st.columns([1.4,.8]); fim=compose(fg,900,600)
            with x: st.image(fim,use_container_width=True)
            with y:
                st.markdown('### Ornament DNA'); st.json({'Мотив':NAMES[fg['motif_idx']],'Композиция':fg['layout'],'Повторы':fg['repeats'],'Масштаб':fg['scale'],'Поворот':f"{fg['rotation']}°",'Интервал':fg['spacing'],'Fitness':round(score(fg),3)}); st.download_button('⬇ Скачать PNG',png(fim),'ornamental_genome.png','image/png',use_container_width=True)
            st.markdown('</div>',unsafe_allow_html=True)
with tabs[1]:
    st.markdown('<div class="cream">',unsafe_allow_html=True); st.markdown('## 🧬 Орнаментальный геном простыми словами'); st.write('Композиция хранится как цифровая ДНК: базовый мотив, масштаб, поворот, число повторов, расстояние и тип композиции. Два дизайна передают часть параметров «потомку», а мутация создаёт новые сочетания.'); st.markdown('**НАСЛЕДИЕ → ГЕНОМ → ЭВОЛЮЦИЯ → ДИЗАЙН**'); st.markdown('</div>',unsafe_allow_html=True)
with tabs[2]:
    st.markdown('<div class="cream">',unsafe_allow_html=True); st.markdown('## 🏛 Библиотека базовых мотивов'); st.caption('21 мотив выделен из загруженного вами листа. Часть названий пока рабочая — перед конкурсом нужно сверить каждое название и источник.'); cols=st.columns(7)
    for i,n in enumerate(NAMES):
        with cols[i%7]: st.image(motif(i,'#143C4A',140),use_container_width=True); st.caption(n)
    st.markdown('</div>',unsafe_allow_html=True)
with tabs[3]:
    st.markdown('<div class="cream">',unsafe_allow_html=True); st.markdown('## 📁 Мои дизайны'); st.write('В этой версии финальный дизайн скачивается в PNG. Постоянные аккаунты и облачная библиотека — следующий технический этап.'); st.markdown('</div>',unsafe_allow_html=True)
with tabs[4]:
    st.markdown('<div class="cream">',unsafe_allow_html=True); st.markdown('## ✨ ИИ-профиль пользователя'); st.write('Пользователь отмечает понравившиеся варианты. Эти оценки могут обучать персональную модель предпочтений и ранжировать следующие поколения.'); st.markdown('</div>',unsafe_allow_html=True)
with tabs[5]:
    st.markdown('<div class="cream">',unsafe_allow_html=True); st.markdown('## 📊 Исследование: GA против случайного поиска'); trials=st.slider('Независимых запусков',5,30,10)
    if st.button('▶ Запустить сравнение'):
        import pandas as pd
        rows=[]
        for t in range(trials):
            rnd=max(score(x) for x in [new_genome(mi,pal,lay) for _ in range(60)])
            pop=[new_genome(mi,pal,lay) for _ in range(12)]
            for _ in range(4):
                parents=sorted(pop,key=score,reverse=True)[:4]; pop=[cross(*random.sample(parents,2)) for _ in range(12)]
            ga=max(score(x) for x in pop); rows.append({'Запуск':t+1,'GA':ga,'Random':rnd})
        df=pd.DataFrame(rows); st.line_chart(df.set_index('Запуск')); st.dataframe(df,use_container_width=True,hide_index=True); st.metric('Среднее преимущество GA',f"{(df.GA-df.Random).mean():+.3f}")
    st.markdown('</div>',unsafe_allow_html=True)
