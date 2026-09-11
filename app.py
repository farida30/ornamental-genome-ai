import streamlit as st
import sqlite3, hashlib, json, math, random, io
from pathlib import Path
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw
from sklearn.ensemble import RandomForestRegressor

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / 'ornamental_genome.db'

st.set_page_config(page_title='ORNAMENTAL GENOME — AI ETHNO DESIGN LAB', page_icon='🧬', layout='wide')

st.markdown('''
<style>
:root {--gold:#f4c95d;--pink:#ff5c8a;--cyan:#62e6e6;--card:#171a22;--muted:#aeb7c7;}
.stApp{background:radial-gradient(circle at 10% 10%,rgba(98,230,230,.08),transparent 28%),radial-gradient(circle at 90% 5%,rgba(255,92,138,.08),transparent 32%),linear-gradient(180deg,#0b0d12 0%,#11151d 100%);color:#f4f7fb}
.block-container{padding-top:1.2rem;padding-bottom:3rem;max-width:1450px}
.og-hero{border:1px solid rgba(255,255,255,.08);border-radius:28px;padding:34px 36px;background:linear-gradient(135deg,rgba(244,201,93,.12),rgba(255,92,138,.08),rgba(98,230,230,.08));box-shadow:0 20px 60px rgba(0,0,0,.25);margin-bottom:18px}
.og-kicker{font-size:.8rem;font-weight:800;letter-spacing:.18em;color:#f4c95d}.og-title{font-size:2.6rem;font-weight:900;line-height:1.05;margin:.25rem 0}.og-sub{color:#c6ceda;font-size:1.02rem;max-width:900px}
.og-card{background:rgba(23,26,34,.93);border:1px solid rgba(255,255,255,.08);border-radius:22px;padding:18px}.og-pill{display:inline-block;padding:6px 10px;border-radius:999px;background:rgba(244,201,93,.13);color:#f4c95d;font-size:.78rem;font-weight:700;margin:2px 4px 2px 0}.og-small{color:#aeb7c7;font-size:.88rem}
div[data-testid='stButton'] button,div[data-testid='stDownloadButton'] button{border-radius:14px;font-weight:800}
</style>
''', unsafe_allow_html=True)

# ---------- database ----------
def db():
    con=sqlite3.connect(DB_PATH,check_same_thread=False); con.row_factory=sqlite3.Row; return con

def init_db():
    con=db(); cur=con.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT UNIQUE NOT NULL,display_name TEXT NOT NULL,password_hash TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    cur.execute('CREATE TABLE IF NOT EXISTS ratings(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,genome_json TEXT NOT NULL,liked INTEGER NOT NULL DEFAULT 0,rating REAL,created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    cur.execute('CREATE TABLE IF NOT EXISTS designs(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,name TEXT NOT NULL,motif TEXT NOT NULL,genome_json TEXT NOT NULL,svg TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    con.commit(); con.close()
init_db()

def phash(p): return hashlib.sha256(('OG::'+p).encode()).hexdigest()
def register_user(u,d,p):
    u=u.strip().lower()
    if len(u)<3 or len(p)<4:return False,'Логин — минимум 3 символа, пароль — минимум 4.'
    try:
        con=db(); con.execute('INSERT INTO users(username,display_name,password_hash) VALUES(?,?,?)',(u,d.strip() or u,phash(p))); con.commit(); con.close(); return True,'Аккаунт создан.'
    except sqlite3.IntegrityError:return False,'Такой логин уже существует.'
def login_user(u,p):
    con=db(); row=con.execute('SELECT * FROM users WHERE username=? AND password_hash=?',(u.strip().lower(),phash(p))).fetchone(); con.close(); return dict(row) if row else None
def save_rating(uid,g,liked,rating=None):
    con=db(); con.execute('INSERT INTO ratings(user_id,genome_json,liked,rating) VALUES(?,?,?,?)',(uid,json.dumps(g,ensure_ascii=False),int(liked),rating)); con.commit(); con.close()
def get_ratings(uid):
    con=db(); rows=con.execute('SELECT * FROM ratings WHERE user_id=? ORDER BY id',(uid,)).fetchall(); con.close(); return [dict(r) for r in rows]
def save_design(uid,name,motif,g,svg):
    con=db(); con.execute('INSERT INTO designs(user_id,name,motif,genome_json,svg) VALUES(?,?,?,?,?)',(uid,name,motif,json.dumps(g,ensure_ascii=False),svg)); con.commit(); con.close()
def get_designs(uid):
    con=db(); rows=con.execute('SELECT * FROM designs WHERE user_id=? ORDER BY id DESC',(uid,)).fetchall(); con.close(); return [dict(r) for r in rows]

MOTIFS={
'Қошқар мүйіз':{'category':'Зооморфный','note':'Стилизованный мотив рогов. В прототипе используется авторская параметрическая векторизация.'},
'Қос мүйіз':{'category':'Зооморфный','note':'Парная композиция рогов; удобна для зеркальной симметрии.'},
'Тұмарша':{'category':'Геометрический','note':'Треугольная композиционная основа; в прототипе — геометрическая интерпретация.'},
'Ирек':{'category':'Геометрический','note':'Ломаный/волнообразный ритм, удобный для бордюрных паттернов.'},
'Жұлдыз':{'category':'Космогонический','note':'Звёздчатая геометрическая структура.'}}
PRODUCTS=['Постер','Упаковка','Шоппер','Обложка','Соцсети','Фирменный паттерн']
STYLES=['Balanced Ethno','Minimal Ethno','Bold Graphic','Editorial','Festival']
LAYOUTS=['Бордюр','Розетка','Сетка','Центральная']
PALETTES={'Heritage Gold':['#0B1B2B','#F4C95D','#E9E2D0'],'Steppe':['#2E4B3F','#C7A46A','#F2E9D7'],'Modern Red':['#201A1A','#D94B4B','#F4EDE3'],'Sky':['#103D5A','#5CC8D7','#F1D8A5'],'Monochrome':['#111111','#F4F4F4','#8C8C8C']}

def random_genome(motif,style,layout,palette):
    bias={'Minimal Ethno':(.65,.45),'Balanced Ethno':(.85,.62),'Bold Graphic':(1,.78),'Editorial':(.78,.58),'Festival':(1.05,.82)}[style]
    return {'motif':motif,'style':style,'layout':layout,'palette':palette,'scale':round(random.uniform(bias[0]*.78,bias[0]*1.18),3),'rotation':random.choice([0,15,30,45,60,90]),'repeats':random.randint(4,12),'spacing':round(random.uniform(.72,1.35),3),'density':round(min(1,max(.2,random.gauss(bias[1],.12))),3),'curve':round(random.uniform(.55,1),3),'stroke':round(random.uniform(2,5),2),'symmetry':random.choice([0,1,2]),'layout_idx':LAYOUTS.index(layout),'seed':random.randint(1,999999)}

def feature_vector(g):
    return [list(MOTIFS).index(g['motif']),STYLES.index(g['style']),list(PALETTES).index(g['palette']),g['scale'],g['rotation']/90,g['repeats']/12,g['spacing'],g['density'],g['curve'],g['stroke']/5,g['symmetry']/2,g['layout_idx']/3]

def personal_model(uid):
    rows=get_ratings(uid);X=[];y=[]
    for r in rows:
        g=json.loads(r['genome_json']); X.append(feature_vector(g)); y.append(float(r['rating']) if r['rating'] is not None else float(r['liked']))
    if len(X)<8 or len(set(y))<2:return None,len(X)
    m=RandomForestRegressor(n_estimators=160,random_state=42,max_depth=7);m.fit(np.array(X),np.array(y));return m,len(X)
def ai_match(model,g): return None if model is None else float(np.clip(model.predict([feature_vector(g)])[0],0,1))
def structure_score(g):
    s_sym=[.65,.90,.94][g['symmetry']]; target={'Minimal Ethno':.45,'Balanced Ethno':.62,'Bold Graphic':.78,'Editorial':.58,'Festival':.82}[g['style']]; s_density=max(0,1-abs(g['density']-target)/.7);s_repeat=1-min(abs(g['repeats']-8)/10,1);s_clean=1-min(max(g['scale']*g['density']-.85,0),.5);return float(np.clip(.30*s_sym+.26*s_density+.22*s_repeat+.22*s_clean,0,1))
def novelty_score(g): return float(np.clip(.25*(g['rotation']/90)+.25*abs(g['spacing']-1)+.25*abs(g['density']-.6)+.25*abs(g['curve']-.75),0,1))
def total_score(g,model=None):
    s=structure_score(g);n=novelty_score(g);p=ai_match(model,g);t=.78*s+.22*n if p is None else .62*s+.18*n+.20*p;return t,s,n,p

def crossover(a,b):
    c=dict(a)
    for k in ['scale','rotation','repeats','spacing','density','curve','stroke','symmetry','layout_idx']:c[k]=a[k] if random.random()<.5 else b[k]
    c['layout']=LAYOUTS[int(c['layout_idx'])];c['seed']=random.randint(1,999999);return c

def mutate(g,rate=.18):
    c=dict(g)
    if random.random()<rate:c['scale']=round(float(np.clip(c['scale']+random.gauss(0,.08),.45,1.35)),3)
    if random.random()<rate:c['rotation']=int(np.clip(c['rotation']+random.choice([-15,15,30]),0,90))
    if random.random()<rate:c['repeats']=int(np.clip(c['repeats']+random.choice([-2,-1,1,2]),3,14))
    if random.random()<rate:c['spacing']=round(float(np.clip(c['spacing']+random.gauss(0,.08),.62,1.5)),3)
    if random.random()<rate:c['density']=round(float(np.clip(c['density']+random.gauss(0,.07),.2,1)),3)
    if random.random()<rate:c['curve']=round(float(np.clip(c['curve']+random.gauss(0,.08),.4,1.2)),3)
    if random.random()<rate:c['stroke']=round(float(np.clip(c['stroke']+random.gauss(0,.5),1.5,6)),2)
    if random.random()<rate:c['symmetry']=random.choice([0,1,2])
    return c

def motif_svg(motif,stroke='#F4C95D',sw=4):
    if motif=='Қошқар мүйіз': path='M 60 78 C 42 78,34 66,36 52 C 38 38,52 32,61 39 C 70 46,69 58,61 63 C 54 68,45 64,45 57 C 45 51,50 47,55 48 C 63 49,68 56,71 66 C 75 80,84 89,99 91'
    elif motif=='Қос мүйіз': path='M60 76 C45 77 34 67 35 53 C36 39 48 33 59 40 C67 45 67 57 59 62 C50 67 43 62 44 55 M60 76 C75 77 86 67 85 53 C84 39 72 33 61 40 C53 45 53 57 61 62 C70 67 77 62 76 55'
    elif motif=='Тұмарша': path='M60 22 L101 94 L19 94 Z M60 42 L82 81 L38 81 Z M60 58 L70 76 L50 76 Z'
    elif motif=='Ирек': path='M10 70 L28 45 L46 70 L64 45 L82 70 L100 45 L112 61'
    else:
        pts=[]
        for i in range(10):
            a=-math.pi/2+i*math.pi/5;r=42 if i%2==0 else 18;pts.append((60+r*math.cos(a),60+r*math.sin(a)))
        path='M '+' L '.join(f'{x:.1f} {y:.1f}' for x,y in pts)+' Z'
    return f'<g><path d="{path}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/></g>'
def transform_group(x,y,scale,rot,content): return f'<g transform="translate({x:.2f},{y:.2f}) rotate({rot:.2f}) scale({scale:.3f}) translate(-60,-60)">{content}</g>'
def render_svg(g,width=760,height=460):
    bg,main,accent=PALETTES[g['palette']];motif=motif_svg(g['motif'],main,g['stroke']);groups=[];n=max(3,int(g['repeats']));sc=max(.35,min(1.2,g['scale']));layout=g['layout']
    if layout=='Бордюр':
        y=height/2;gap=width/(n+1)
        for i in range(n):
            x=gap*(i+1);rr=g['rotation']*((-1)**i if g['symmetry']==1 else 1);groups.append(transform_group(x-60,y-60,sc*.78,rr,motif))
    elif layout=='Розетка':
        R=min(width,height)*.27*g['spacing']
        for i in range(n):
            a=2*math.pi*i/n;x=width/2+R*math.cos(a)-60;y=height/2+R*math.sin(a)-60;groups.append(transform_group(x,y,sc*.72,math.degrees(a)+g['rotation'],motif))
    elif layout=='Сетка':
        cols=max(2,int(math.sqrt(n*1.6)));rows=max(2,math.ceil(n/cols));sx=width/(cols+1);sy=height/(rows+1);k=0
        for r in range(rows):
            for c in range(cols):
                if k>=n:break
                x=sx*(c+1)-60;y=sy*(r+1)-60;rot=g['rotation']+(180 if (g['symmetry']==1 and (r+c)%2) else 0);groups.append(transform_group(x,y,sc*.58,rot,motif));k+=1
    else:
        groups.append(transform_group(width/2-60,height/2-60,sc*1.75,g['rotation'],motif))
        for i in range(min(n,8)):
            a=2*math.pi*i/min(n,8);R=min(width,height)*.28;x=width/2+R*math.cos(a)-60;y=height/2+R*math.sin(a)-60;groups.append(transform_group(x,y,sc*.48,math.degrees(a)+g['rotation'],motif))
    border=f'<rect x="20" y="20" width="{width-40}" height="{height-40}" rx="24" fill="none" stroke="{accent}" opacity=".22" stroke-width="2"/>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="100%" height="100%" rx="28" fill="{bg}"/>{border}{"".join(groups)}</svg>'

def svg_to_png_fallback(g,width=1000,height=600):
    bg,main,_=PALETTES[g['palette']];img=Image.new('RGB',(width,height),bg);d=ImageDraw.Draw(img);n=max(3,int(g['repeats']));w=max(2,int(g['stroke']))
    if g['layout']=='Бордюр':
        for i in range(n):
            x=(i+1)*width/(n+1);y=height/2;r=28+24*g['scale'];d.arc((x-r,y-r,x+r,y+r),180,520,fill=main,width=w);d.line((x,y,x+r*.9,y+r*.65),fill=main,width=w)
    elif g['layout']=='Розетка':
        R=min(width,height)*.28
        for i in range(n):
            a=2*math.pi*i/n;x=width/2+R*math.cos(a);y=height/2+R*math.sin(a);r=24+20*g['scale'];d.arc((x-r,y-r,x+r,y+r),170,520,fill=main,width=w)
    elif g['layout']=='Сетка':
        cols=max(2,int(math.sqrt(n*1.6)));rows=max(2,math.ceil(n/cols))
        for r0 in range(rows):
            for c0 in range(cols):
                x=(c0+1)*width/(cols+1);y=(r0+1)*height/(rows+1);r=20+16*g['scale'];d.arc((x-r,y-r,x+r,y+r),180,510,fill=main,width=w)
    else:
        r=min(width,height)*.22;cx,cy=width/2,height/2
        for i in range(n):
            a=2*math.pi*i/n;x=cx+r*math.cos(a);y=cy+r*math.sin(a);d.line((cx,cy,x,y),fill=main,width=w)
    out=io.BytesIO();img.save(out,format='PNG');return out.getvalue()

def design_card(g,model=None):
    score,struct,nov,pm=total_score(g,model);st.components.v1.html(render_svg(g,540,310),height=325);c1,c2,c3=st.columns(3);c1.metric('Fitness',f'{score:.3f}');c2.metric('Structure',f'{struct:.2f}');c3.metric('AI Match','—' if pm is None else f'{pm*100:.0f}%');return score

for k,v in {'user':None,'guest':False,'population':[],'generation':0,'selected':[],'final_genome':None}.items():
    if k not in st.session_state:st.session_state[k]=v

def auth_screen():
    st.markdown('''<div class="og-hero"><div class="og-kicker">CREATIVE TECH • KAZAKH ETHNO DESIGN</div><div class="og-title">🧬 ORNAMENTAL GENOME</div><div class="og-sub">AI ETHNO DESIGN LAB — персональная эволюционная студия современного графического дизайна на основе казахских орнаментальных мотивов.</div></div>''',unsafe_allow_html=True)
    c1,c2=st.columns([1.1,1])
    with c1:
        st.markdown('### Почему это не просто генератор');st.markdown('''<div class="og-card"><span class="og-pill">Ornament DNA</span><span class="og-pill">Evolution</span><span class="og-pill">Personal AI</span><span class="og-pill">My Studio</span><span class="og-pill">SVG / PNG Export</span><p class="og-small">Алгоритм сохраняет происхождение мотива, эволюционно меняет композицию, а персональная модель учится на выборе пользователя.</p></div>''',unsafe_allow_html=True)
        st.write('')
        if st.button('🚀 Попробовать без регистрации',use_container_width=True):st.session_state.guest=True;st.rerun()
    with c2:
        t1,t2=st.tabs(['Войти','Регистрация'])
        with t1:
            u=st.text_input('Логин',key='login_u');p=st.text_input('Пароль',type='password',key='login_p')
            if st.button('Войти',use_container_width=True):
                row=login_user(u,p)
                if row:st.session_state.user=row;st.session_state.guest=False;st.rerun()
                else:st.error('Неверный логин или пароль.')
        with t2:
            d=st.text_input('Имя',key='reg_d');u=st.text_input('Придумайте логин',key='reg_u');p=st.text_input('Придумайте пароль',type='password',key='reg_p')
            if st.button('Создать аккаунт',use_container_width=True):
                ok,msg=register_user(u,d,p);(st.success if ok else st.error)(msg)
    st.info('Прототип конкурса: локальная SQLite-регистрация. Для публичного сервиса базу пользователей нужно вынести в облако (например, Supabase).')

if not st.session_state.user and not st.session_state.guest:auth_screen();st.stop()
user=st.session_state.user;is_guest=st.session_state.guest;display_name='Гость' if is_guest else user['display_name'];user_id=None if is_guest else int(user['id'])
with st.sidebar:
    st.markdown('## 🧬 ORNAMENTAL GENOME');st.caption('AI ETHNO DESIGN LAB');st.success(f'Профиль: {display_name}')
    if not is_guest:model,nlearn=personal_model(user_id);st.metric('Обучающих выборов',nlearn);st.caption('После 8+ разнообразных оценок включается персональная ML-модель.')
    else:model,nlearn=None,0;st.warning('Гостевой режим: библиотека и AI-профиль не сохраняются.')
    page=st.radio('Навигация',['🎨 Design Studio','🧬 Evolution Lab','✨ AI Designer','📁 My Studio','🏛 Ornament Library','📊 Research Lab','ℹ️ О проекте'])
    if st.button('Выйти',use_container_width=True):st.session_state.user=None;st.session_state.guest=False;st.rerun()

if page=='🎨 Design Studio':
    st.markdown('''<div class="og-hero"><div class="og-kicker">STEP 1 • CREATE</div><div class="og-title">Создай современный дизайн с культурным кодом Казахстана</div><div class="og-sub">Выберите мотив, назначение и визуальный характер. Система создаст стартовое поколение — не одну картинку, а пространство вариантов.</div></div>''',unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4);motif=c1.selectbox('Базовый мотив',list(MOTIFS));product=c2.selectbox('Продукт',PRODUCTS);style=c3.selectbox('Стиль',STYLES,index=1);palette=c4.selectbox('Палитра',list(PALETTES));layout=st.selectbox('Композиция',LAYOUTS,index=1);st.caption(MOTIFS[motif]['note'])
    if st.button('🧬 СОЗДАТЬ ПОКОЛЕНИЕ',type='primary',use_container_width=True):st.session_state.population=[random_genome(motif,style,layout,palette) for _ in range(8)];st.session_state.generation=1;st.session_state.selected=[];st.session_state.final_genome=None
    if st.session_state.population:
        st.markdown(f"### Поколение {st.session_state.generation}");st.caption('Выберите 2–4 варианта, которые хотите развивать дальше.');cols=st.columns(4)
        for i,g in enumerate(st.session_state.population):
            with cols[i%4]:
                design_card(g,model);active=i in st.session_state.selected
                if st.button(('✅ ' if active else '❤️ ')+f'A{i+1:02d}',key=f'pick_{st.session_state.generation}_{i}',use_container_width=True):
                    if i in st.session_state.selected:st.session_state.selected.remove(i)
                    else:st.session_state.selected.append(i)
                    if user_id is not None:save_rating(user_id,g,1,1.0)
                    st.rerun()
        cc1,cc2=st.columns([2,1])
        with cc1:
            if st.button('⚡ Развить выбранные в следующем поколении',use_container_width=True):
                sel=[st.session_state.population[i] for i in st.session_state.selected]
                if len(sel)<2:st.warning('Выберите минимум 2 варианта.')
                else:
                    new=[]
                    while len(new)<8:
                        a,b=random.sample(sel,2);new.append(mutate(crossover(a,b),.22))
                    st.session_state.population=new;st.session_state.generation+=1;st.session_state.selected=[];st.rerun()
        with cc2:
            if st.button('🏆 Выбрать лучший автоматически',use_container_width=True):st.session_state.final_genome=max(st.session_state.population,key=lambda g:total_score(g,model)[0]);st.success('Финальный кандидат выбран.')
    if st.session_state.final_genome:
        g=st.session_state.final_genome;st.markdown('## 🏆 Финальный дизайн');a,b=st.columns([1.25,.75])
        with a:design_card(g,model)
        with b:
            st.markdown('### Ornament DNA');st.json({k:g[k] for k in ['motif','style','layout','palette','scale','rotation','repeats','spacing','density','curve','symmetry']});svg=render_svg(g,1000,600);png=svg_to_png_fallback(g,1000,600);st.download_button('⬇ Скачать SVG',svg,file_name='ornamental_genome.svg',mime='image/svg+xml',use_container_width=True);st.download_button('⬇ Скачать PNG',png,file_name='ornamental_genome.png',mime='image/png',use_container_width=True)
            if user_id is not None:
                nm=st.text_input('Название проекта','Мой этнодизайн')
                if st.button('💾 Сохранить в My Studio',use_container_width=True):save_design(user_id,nm,g['motif'],g,svg);st.success('Сохранено в My Studio.')
elif page=='🧬 Evolution Lab':
    st.markdown('## 🧬 Evolution Lab');st.write('Здесь видно, **почему проект называется «Орнаментальный геном»**: два родителя передают гены потомку, затем происходит мутация.');motif=st.selectbox('Мотив',list(MOTIFS),key='evo_m')
    if 'evo_parents' not in st.session_state:st.session_state.evo_parents=(random_genome(motif,'Balanced Ethno','Розетка','Heritage Gold'),random_genome(motif,'Minimal Ethno','Бордюр','Sky'))
    if st.button('🎲 Новые родители'):st.session_state.evo_parents=(random_genome(motif,random.choice(STYLES),random.choice(LAYOUTS),random.choice(list(PALETTES))),random_genome(motif,random.choice(STYLES),random.choice(LAYOUTS),random.choice(list(PALETTES))))
    a,b=st.session_state.evo_parents;child=mutate(crossover(a,b),.28);c1,c2,c3=st.columns(3)
    with c1:st.subheader('Родитель A');design_card(a,model)
    with c2:st.subheader('Родитель B');design_card(b,model)
    with c3:st.subheader('Потомок');design_card(child,model)
    st.markdown('#### Сравнение генов');st.dataframe(pd.DataFrame([{'Ген':k,'A':a[k],'B':b[k],'Потомок':child[k]} for k in ['scale','rotation','repeats','spacing','density','curve','stroke','symmetry']]),use_container_width=True,hide_index=True)
elif page=='✨ AI Designer':
    st.markdown('## ✨ AI Designer — мой Design DNA')
    if is_guest:st.warning('Персональный AI-профиль работает после регистрации.')
    else:
        model,nlearn=personal_model(user_id);st.progress(min(nlearn/20,1.0),text=f'Собрано {nlearn} выборов. Для прототипа модель включается после 8.');st.write('ИИ не определяет «правильность» культуры. Он изучает **индивидуальные дизайнерские предпочтения пользователя**.');qmotif=st.selectbox('Мотив для калибровки',list(MOTIFS),key='ai_m');pair=[random_genome(qmotif,'Minimal Ethno',random.choice(LAYOUTS),random.choice(list(PALETTES))),random_genome(qmotif,'Bold Graphic',random.choice(LAYOUTS),random.choice(list(PALETTES)))];c1,c2=st.columns(2)
        for i,g in enumerate(pair):
            with [c1,c2][i]:
                design_card(g,model);ca,cb=st.columns(2)
                if ca.button('❤️ Нравится',key=f'like_{i}',use_container_width=True):save_rating(user_id,g,1,1.0);st.rerun()
                if cb.button('✖ Не моё',key=f'dislike_{i}',use_container_width=True):save_rating(user_id,g,0,0.0);st.rerun()
elif page=='📁 My Studio':
    st.markdown('## 📁 My Studio')
    if is_guest:st.warning('В гостевом режиме проекты не сохраняются. Создайте аккаунт.')
    else:
        designs=get_designs(user_id)
        if not designs:st.info('Пока пусто. Сохраните финальный дизайн из Design Studio.')
        else:
            cols=st.columns(3)
            for i,d in enumerate(designs):
                with cols[i%3]:
                    st.markdown(f"### {d['name']}");st.components.v1.html(d['svg'],height=280);st.caption(f"{d['motif']} • {d['created_at']}");st.download_button('SVG',d['svg'],file_name=f"OG_{d['id']}.svg",mime='image/svg+xml',key=f"dsvg_{d['id']}",use_container_width=True)
elif page=='🏛 Ornament Library':
    st.markdown('## 🏛 Ornament Library');st.write('Библиотека мотивов — культурная база проекта. В конкурсной версии каждый мотив должен иметь источник и паспорт происхождения.')
    for name,meta in MOTIFS.items():
        with st.expander(f"{name} — {meta['category']}"):
            demo=random_genome(name,'Balanced Ethno','Центральная','Heritage Gold');c1,c2=st.columns([.7,1.3])
            with c1:st.components.v1.html(render_svg(demo,440,280),height=295)
            with c2:st.write(meta['note']);st.markdown('**Статус в прототипе:** авторская параметрическая интерпретация для вычислительного эксперимента; не музейная копия.');st.markdown('**Перед финальной подачей:** добавить источник, страницу/объект, автора векторизации и допустимые преобразования.')
elif page=='📊 Research Lab':
    st.markdown('## 📊 Research Lab — GA vs Random');st.write('Научная часть продукта: при одинаковом вычислительном бюджете сравниваем эволюционный поиск со случайным.');r1,r2,r3=st.columns(3);motif=r1.selectbox('Мотив',list(MOTIFS),key='res_m');trials=r2.slider('Независимых запусков',5,30,12);budget=r3.slider('Кандидатов в запуске',30,180,80,10)
    if st.button('▶ Провести эксперимент',type='primary'):
        data=[];prog=st.progress(0)
        for t in range(trials):
            candidates=[random_genome(motif,'Balanced Ethno','Розетка','Heritage Gold') for _ in range(budget)];rnd=max(total_score(g,None)[0] for g in candidates);popn=10;pop=[random_genome(motif,'Balanced Ethno','Розетка','Heritage Gold') for _ in range(popn)];evals=popn
            while evals+popn<=budget:
                pop=sorted(pop,key=lambda g:total_score(g,None)[0],reverse=True);parents=pop[:4];new=parents[:2]
                while len(new)<popn:
                    a,b=random.sample(parents,2);new.append(mutate(crossover(a,b),.22))
                pop=new;evals+=popn
            ga=max(total_score(g,None)[0] for g in pop);data.append({'run':t+1,'GA':ga,'Random':rnd,'difference':ga-rnd});prog.progress((t+1)/trials)
        st.session_state['research_df']=pd.DataFrame(data)
    if 'research_df' in st.session_state:
        df=st.session_state['research_df'];c1,c2,c3=st.columns(3);c1.metric('Средний GA',f'{df.GA.mean():.3f}');c2.metric('Средний Random',f'{df.Random.mean():.3f}');c3.metric('Преимущество GA',f'{df.difference.mean():+.3f}');st.line_chart(df.set_index('run')[['GA','Random']]);st.dataframe(df,use_container_width=True,hide_index=True);st.download_button('⬇ Скачать CSV',df.to_csv(index=False).encode('utf-8-sig'),file_name='ga_vs_random.csv',mime='text/csv')
else:
    st.markdown('''<div class="og-hero"><div class="og-kicker">SCIENCE × DESIGN × CULTURE</div><div class="og-title">О проекте</div><div class="og-sub">«Орнаментальный геном» — исследовательский прототип генеративного этнодизайна. Традиционный мотив выступает источником, алгоритм — инструментом поиска композиционных вариантов, человек — финальным дизайнером.</div></div>''',unsafe_allow_html=True)
    st.markdown('''### Что делает продукт
1. Кодирует композицию набором генов.
2. Создаёт популяцию дизайнерских вариантов.
3. Применяет selection → crossover → mutation.
4. Позволяет пользователю формировать персональный Design DNA.
5. Сохраняет проекты в My Studio.
6. Экспортирует дизайн в SVG и PNG.
7. Отдельно проводит научный эксперимент GA vs Random.

### Важное ограничение
Программа не объявляет сгенерированный результат новым традиционным орнаментом и не оценивает культурную «правильность». Встроенные контуры — авторские стилизованные модели для вычислительного прототипа. Для конкурсной финальной версии библиотека должна быть заменена/уточнена на собственные векторизации документированных источников.
''')
