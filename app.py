import streamlit as st
import sqlite3, hashlib, json, math, random, io, time
from pathlib import Path
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw
from sklearn.ensemble import RandomForestRegressor

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / 'ornamental_genome.db'

st.set_page_config(page_title='ORNAMENTAL GENOME AI — Kazakh Creative Lab', page_icon='✦', layout='wide', initial_sidebar_state='collapsed')

# =========================================================
# DESIGN SYSTEM — intentionally close to the supplied mockup
# =========================================================
st.markdown(r'''
<style>
:root{
 --navy:#032f40; --navy2:#063c50; --deep:#052937; --cyan:#10c3df;
 --gold:#e5ad45; --cream:#f8f2e7; --red:#d63a34; --teal:#11778a;
 --ink:#0c3d51; --line:rgba(255,255,255,.13); --soft:#eae5d9;
}
html,body,[class*="css"]{font-family:Inter,Segoe UI,Arial,sans-serif}
.stApp{background:linear-gradient(180deg,#06394b 0%,#052f3e 100%);color:white}
[data-testid="stHeader"]{background:transparent;height:0}
.block-container{padding:0!important;max-width:100%!important}
#MainMenu,footer{visibility:hidden}

/* top navigation */
.og-top{height:78px;background:linear-gradient(90deg,#022e3e,#07394b);border-bottom:1px solid rgba(255,255,255,.12);display:flex;align-items:center;padding:0 26px;gap:28px;position:sticky;top:0;z-index:50}
.og-brand{min-width:285px;display:flex;align-items:center;gap:14px}
.og-logo{width:47px;height:47px;border:2px solid #e5ad45;border-radius:15px;display:grid;place-items:center;color:#e5ad45;font-size:28px;transform:rotate(45deg)}
.og-logo span{transform:rotate(-45deg)}
.og-brand b{font-family:Georgia,serif;font-size:21px;line-height:1.05;color:#f8e6bd;letter-spacing:.04em}
.og-brand small{display:block;color:#d6c79f;letter-spacing:.19em;font-size:10px;margin-top:4px}
.og-nav{display:flex;gap:9px;flex-wrap:wrap;align-items:center}
.og-nav span{padding:10px 14px;border-radius:15px;color:#e8f1f4;font-size:14px;white-space:nowrap}
.og-nav span.active{background:#0584a4;border:1px solid #1ed1eb;box-shadow:0 0 0 1px rgba(16,195,223,.13) inset}
.og-user{margin-left:auto;color:#f1f6f7;font-weight:700}

/* overall 3-column studio */
.og-shell{padding:14px 18px 18px}
.og-section-title{display:flex;align-items:center;gap:9px;font-size:18px;font-weight:850;margin:14px 0 10px;color:#fff}
.og-step{width:27px;height:27px;border-radius:999px;background:#19b8d5;display:grid;place-items:center;font-weight:900;font-size:13px;box-shadow:0 4px 14px rgba(25,184,213,.25)}
.og-panel{background:rgba(0,36,50,.72);border:1px solid rgba(112,201,223,.17);border-radius:19px;padding:14px;box-shadow:0 15px 38px rgba(0,0,0,.16)}
.og-main-card{background:#f7f2e8;border:1px solid #d5d8d2;border-radius:20px;padding:16px;color:#07384b;box-shadow:0 14px 38px rgba(0,0,0,.2)}
.og-hero{height:184px;border-radius:0 0 22px 22px;overflow:hidden;padding:24px 28px;position:relative;background:radial-gradient(circle at 22% 20%,rgba(221,173,78,.28),transparent 24%),linear-gradient(120deg,rgba(5,56,73,.86),rgba(5,54,70,.96)),repeating-linear-gradient(45deg,rgba(229,173,69,.08) 0 2px,transparent 2px 18px)}
.og-hero:after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,transparent 0 60%,rgba(229,173,69,.07));pointer-events:none}
.og-hero h1{font-family:Georgia,serif;color:white;font-size:39px;margin:0 0 7px;line-height:1.05}
.og-hero p{font-size:18px;color:#e4f0f1;margin:0}
.og-hero .motto{position:absolute;right:35px;bottom:27px;color:#f6c75c;font-family:Georgia,serif;font-style:italic;font-size:22px;text-align:center;line-height:1.25;transform:rotate(-4deg)}

/* motif cards */
.og-motif-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}
.og-motif-card{background:#f6f0e5;border:1px solid #d7ccba;border-radius:12px;padding:7px 5px;text-align:center;min-height:100px;color:#07394a}
.og-motif-card.active{outline:2px solid #e7b24e;box-shadow:0 0 0 3px rgba(229,173,69,.13)}
.og-motif-card svg{width:56px;height:56px}.og-motif-card b{font-size:12px;display:block;margin-top:2px}

/* product buttons and chips */
.og-product-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.og-product{border:1px solid rgba(153,216,231,.26);background:#053344;border-radius:11px;text-align:center;padding:12px 4px;color:#f0f6f7;font-size:12px}.og-product.active{border-color:#12c2df;box-shadow:0 0 12px rgba(18,194,223,.19)}
.og-icon{font-size:24px;display:block;margin-bottom:5px}
.og-chips{display:flex;gap:7px}.og-chip{border:1px solid rgba(155,218,232,.25);padding:8px 11px;border-radius:9px;font-size:12px;color:#d9e8eb}.og-chip.active{border-color:#14c7e3;background:#0a5267;color:white}
.og-swatches{display:flex;gap:9px;margin-top:12px}.og-swatch{width:34px;height:34px;border-radius:7px;border:1px solid rgba(255,255,255,.2)}

/* evolution ribbon */
.og-evo-title{font-weight:900;font-size:18px;margin-bottom:12px;color:#07384b}.og-evo-row{display:grid;grid-template-columns:1fr 45px 1fr 45px 1fr 45px 1fr 45px 1fr;align-items:center;text-align:center;gap:5px}.og-stage small{display:block;font-weight:800;margin-bottom:7px}.og-stage svg{width:78px;height:78px}.og-arrow{font-size:28px;color:#0c5367;font-weight:900}.og-progress-bg{height:15px;border-radius:999px;background:#d8d8cf;margin-top:17px;overflow:hidden;border:1px solid #c3c4bb}.og-progress-fill{height:100%;width:75%;background:linear-gradient(90deg,#006a82,#05bfdc 82%,#b9f7ff);box-shadow:0 0 12px #1ddcf5}

/* generation cards */
.og-gen-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}.og-gen-head h3{font-size:20px;margin:0;color:#07384b}.og-gen-head .sort{border:1px solid #99b8c0;border-radius:9px;padding:7px 12px;background:#fff;font-size:12px}
.og-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px}.og-design{background:#fffaf0;border:1px solid #e1ded4;border-radius:13px;padding:8px;box-shadow:0 5px 10px rgba(20,40,45,.06)}.og-design .art{background:#f5ede1;border-radius:10px;aspect-ratio:1/1;display:grid;place-items:center;overflow:hidden}.og-design svg{width:92%;height:92%}.og-design .meta{display:flex;align-items:end;justify-content:space-between;color:#07384b;margin-top:6px}.og-design .meta b{font-size:12px}.og-design .meta small{font-size:11px;color:#5d7882}.og-heart{font-size:20px;color:#d53455}

/* right cards */
.og-r-title{font-size:17px;font-weight:850;margin:0 0 13px}.og-field{display:flex;align-items:center;justify-content:space-between;margin:10px 0;font-size:13px}.og-field strong{background:#0b4659;border-radius:9px;padding:7px 12px;min-width:80px;text-align:center}.og-motif-info{display:grid;grid-template-columns:82px 1fr;gap:13px;align-items:center}.og-info-thumb{background:#f7f0e4;border-radius:10px;height:125px;display:grid;place-items:center}.og-info-thumb svg{width:70px;height:70px}.og-copy{font-size:13px;color:#dce9eb;line-height:1.45}.og-link{color:#20cce8;font-size:12px;margin-top:5px}.og-pack{height:230px;border-radius:13px;background:radial-gradient(circle at 82% 20%,#b9473f 0 13%,transparent 28%),linear-gradient(135deg,#5a281c,#c67c43 47%,#efe3ce 48% 100%);display:grid;place-items:center;overflow:hidden}.og-box{width:130px;height:175px;background:#f5e4c7;border-radius:2px;box-shadow:0 12px 28px rgba(0,0,0,.28);display:flex;align-items:stretch}.og-box-strip{width:43px;background:#d53b34;display:grid;place-items:center}.og-box-text{flex:1;display:grid;place-items:center;text-align:center;color:#3c2e21;font-family:Georgia,serif;font-size:13px}.og-download{background:#0ab48f;border-radius:10px;padding:13px 12px;text-align:center;font-weight:900;font-size:16px;margin-top:12px}.og-formats{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;margin-top:10px}.og-format{border:1px solid rgba(200,233,238,.3);border-radius:8px;padding:8px 4px;text-align:center;font-size:11px}

/* Streamlit widgets */
div[data-testid="stButton"] button{border-radius:10px;font-weight:800;min-height:40px}
div[data-testid="stButton"] button[kind="primary"]{background:linear-gradient(90deg,#f3c15b,#e5a93e);color:#06364a;border:none;box-shadow:0 8px 20px rgba(229,173,69,.24)}
div[data-testid="stDownloadButton"] button{border-radius:10px;font-weight:800;background:#0bad8a;color:white;border:none}
.stSelectbox div[data-baseweb="select"]>div,.stNumberInput input,.stTextInput input{background:#0b4659!important;color:white!important;border-color:rgba(255,255,255,.12)!important;border-radius:9px!important}
.stSlider{padding-top:0}.stTabs [data-baseweb="tab-list"]{gap:8px}.stTabs [data-baseweb="tab"]{background:#073b4d;border-radius:11px;color:white;padding:8px 14px}

/* auth */
.og-auth-wrap{max-width:1020px;margin:80px auto}.og-auth-card{background:#f7f1e7;color:#06384a;border-radius:24px;padding:28px;box-shadow:0 25px 70px rgba(0,0,0,.3)}

@media(max-width:1150px){.og-grid{grid-template-columns:repeat(3,1fr)}.og-nav span:nth-child(n+5){display:none}.og-brand{min-width:245px}}
</style>
''', unsafe_allow_html=True)

# ---------- database ----------
def db():
    con = sqlite3.connect(DB_PATH, check_same_thread=False); con.row_factory = sqlite3.Row; return con

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
        con=db();con.execute('INSERT INTO users(username,display_name,password_hash) VALUES(?,?,?)',(u,d.strip() or u,phash(p)));con.commit();con.close();return True,'Аккаунт создан.'
    except sqlite3.IntegrityError:return False,'Такой логин уже существует.'
def login_user(u,p):
    con=db();row=con.execute('SELECT * FROM users WHERE username=? AND password_hash=?',(u.strip().lower(),phash(p))).fetchone();con.close();return dict(row) if row else None
def save_rating(uid,g,liked,rating=None):
    con=db();con.execute('INSERT INTO ratings(user_id,genome_json,liked,rating) VALUES(?,?,?,?)',(uid,json.dumps(g,ensure_ascii=False),int(liked),rating));con.commit();con.close()
def get_ratings(uid):
    con=db();rows=con.execute('SELECT * FROM ratings WHERE user_id=? ORDER BY id',(uid,)).fetchall();con.close();return [dict(r) for r in rows]
def save_design(uid,name,motif,g,svg):
    con=db();con.execute('INSERT INTO designs(user_id,name,motif,genome_json,svg) VALUES(?,?,?,?,?)',(uid,name,motif,json.dumps(g,ensure_ascii=False),svg));con.commit();con.close()
def get_designs(uid):
    con=db();rows=con.execute('SELECT * FROM designs WHERE user_id=? ORDER BY id DESC',(uid,)).fetchall();con.close();return [dict(r) for r in rows]

# ---------- product model ----------
MOTIFS={
'Қошқар мүйіз':('Зооморфный','#d63a34'), 'Түйетабан':('Зооморфный','#11778a'), 'Қазмойын':('Зооморфный','#bf8a2e'),
'Құстаңдай':('Зооморфный','#115d4e'), 'Гүл':('Растительный','#d63a34'), 'Тұмарша':('Геометрический','#0d5e73'),
'Жұлдыз':('Космогонический','#bf8a2e'), 'Төртқұлақ':('Космогонический','#147b81'), 'Бітпес':('Космогонический','#8f5a35')}
PRODUCTS=['Логотип','Упаковка','Постер','Текстиль','Сувенир','Соцсети']
STYLES=['Классика','Современный','Минимал']
LAYOUTS=['Розетка','Бордюр','Центральная','Сетка']
PALETTES={'Qazaq Red':['#fff5e5','#d63a34','#0d5e73','#e1aa43'],'Altai Teal':['#f8f0df','#0d5e73','#11778a','#d9a33d'],'Steppe Gold':['#fff4df','#bf8a2e','#7a4d29','#0d5e73'],'Emerald':['#f8f0df','#115d4e','#147b81','#d3a747']}

def random_genome(motif,style='Современный',layout='Розетка',palette='Qazaq Red'):
    bias={'Классика':(.90,.72),'Современный':(.82,.64),'Минимал':(.68,.46)}[style]
    return {'motif':motif,'style':style,'layout':layout,'palette':palette,
            'scale':round(random.uniform(bias[0]*.80,bias[0]*1.18),3),'rotation':random.choice([0,15,30,45,60,90]),
            'repeats':random.randint(4,12),'spacing':round(random.uniform(.75,1.28),3),'density':round(float(np.clip(random.gauss(bias[1],.10),.25,.95)),3),
            'curve':round(random.uniform(.65,1.0),3),'stroke':round(random.uniform(2.5,5.2),2),'symmetry':random.choice([1,2]),'layout_idx':LAYOUTS.index(layout),'seed':random.randint(1,999999)}

def feature_vector(g):
    return [list(MOTIFS).index(g['motif']),STYLES.index(g['style']),list(PALETTES).index(g['palette']),g['scale'],g['rotation']/90,g['repeats']/12,g['spacing'],g['density'],g['curve'],g['stroke']/5,g['symmetry']/2,g['layout_idx']/3]

def personal_model(uid):
    rows=get_ratings(uid);X=[];y=[]
    for r in rows:
        g=json.loads(r['genome_json']);X.append(feature_vector(g));y.append(float(r['rating']) if r['rating'] is not None else float(r['liked']))
    if len(X)<8 or len(set(y))<2:return None,len(X)
    m=RandomForestRegressor(n_estimators=160,random_state=42,max_depth=7);m.fit(np.array(X),np.array(y));return m,len(X)
def ai_match(model,g):return None if model is None else float(np.clip(model.predict([feature_vector(g)])[0],0,1))
def structure_score(g):
    td={'Классика':.72,'Современный':.64,'Минимал':.46}[g['style']]
    sd=max(0,1-abs(g['density']-td)/.6);sr=1-min(abs(g['repeats']-8)/9,1);ss=.94 if g['symmetry']==2 else .88
    return float(np.clip(.36*ss+.34*sd+.30*sr,0,1))
def novelty_score(g):return float(np.clip(.32*g['rotation']/90+.25*abs(g['spacing']-1)+.23*abs(g['density']-.6)+.20*abs(g['curve']-.8),0,1))
def total_score(g,model=None):
    s=structure_score(g);n=novelty_score(g);a=ai_match(model,g);t=.78*s+.22*n if a is None else .60*s+.18*n+.22*a;return float(t),s,n,a

def crossover(a,b):
    c=dict(a)
    for k in ['scale','rotation','repeats','spacing','density','curve','stroke','symmetry','layout_idx']:
        c[k]=a[k] if random.random()<.5 else b[k]
    c['layout']=LAYOUTS[int(c['layout_idx'])];c['seed']=random.randint(1,999999);return c
def mutate(g,rate=.15):
    c=dict(g)
    if random.random()<rate:c['scale']=round(float(np.clip(c['scale']+random.gauss(0,.07),.45,1.3)),3)
    if random.random()<rate:c['rotation']=int(np.clip(c['rotation']+random.choice([-15,15,30]),0,90))
    if random.random()<rate:c['repeats']=int(np.clip(c['repeats']+random.choice([-2,-1,1,2]),3,14))
    if random.random()<rate:c['spacing']=round(float(np.clip(c['spacing']+random.gauss(0,.08),.65,1.45)),3)
    if random.random()<rate:c['density']=round(float(np.clip(c['density']+random.gauss(0,.07),.2,1)),3)
    if random.random()<rate:c['curve']=round(float(np.clip(c['curve']+random.gauss(0,.07),.45,1.15)),3)
    return c

# ---------- ornamental SVG ----------
def motif_core(name, color='#d63a34', accent='#0d5e73'):
    # Deliberately filled, decorative author-created SVG motifs instead of thin line stars.
    if name=='Қошқар мүйіз':
        return f'''<g fill="{color}"><path d="M58 24c-23-4-38 13-36 31 2 17 18 27 34 20 12-5 16-20 8-30-6-8-17-7-21 0-4 7 2 15 9 14 7-1 8-8 5-12 11 4 15 18 8 28-8 13-28 14-39 4C3 59 4 32 23 18 35 9 51 9 62 14z"/><path d="M62 14c11-5 27-5 39 4 19 14 20 41 5 53-11 10-31 9-39-4-7-10-3-24 8-28-3 4-2 11 5 12 7 1 13-7 9-14-4-7-15-8-21 0-8 10-4 25 8 30 16 7 32-3 34-20 2-18-13-35-36-31z"/></g><path d="M60 66l13 15-13 13-13-13z" fill="{accent}"/>'''
    if name=='Түйетабан':
        return f'''<g fill="{color}"><path d="M60 12l10 22 24-5-14 20 18 16-25 2-3 25-10-22-10 22-3-25-25-2 18-16-14-20 24 5z"/></g><circle cx="60" cy="60" r="15" fill="{accent}"/><circle cx="60" cy="60" r="7" fill="#f8f0df"/>'''
    if name=='Қазмойын':
        return f'''<path d="M31 89C17 72 20 47 38 36c13-8 31-5 38 7 6 10 3 22-7 27-8 4-17 1-20-6-3-6 1-12 7-13-2 7 6 12 11 7 8-7 0-17-10-16-12 1-22 14-21 28 1 15 15 24 30 22V89H31z" fill="{color}"/><path d="M71 39c13-11 28-7 33 6-9-6-18-3-23 4z" fill="{accent}"/>'''
    if name=='Құстаңдай':
        return f'''<g fill="{color}"><path d="M60 10l12 26 28-6-17 23 21 18-29 2-5 29-10-27-10 27-5-29-29-2 21-18-17-23 28 6z"/></g><path d="M60 31l8 21 22 8-22 8-8 21-8-21-22-8 22-8z" fill="#f8f0df"/><circle cx="60" cy="60" r="9" fill="{accent}"/>'''
    if name=='Гүл':
        petals=''.join([f'<ellipse cx="60" cy="28" rx="12" ry="22" transform="rotate({i*45} 60 60)" fill="{color}"/>' for i in range(8)])
        return petals+f'<circle cx="60" cy="60" r="15" fill="{accent}"/><circle cx="60" cy="60" r="7" fill="#f8f0df"/>'
    if name=='Тұмарша':
        return f'''<path d="M60 13L106 97H14z" fill="{color}"/><path d="M60 34l25 48H35z" fill="#f8f0df"/><path d="M60 48l14 28H46z" fill="{accent}"/><circle cx="60" cy="60" r="5" fill="#f8f0df"/>'''
    if name=='Жұлдыз':
        pts=[]
        for i in range(16):
            a=-math.pi/2+i*math.pi/8;r=46 if i%2==0 else 25;pts.append(f'{60+r*math.cos(a):.1f},{60+r*math.sin(a):.1f}')
        return f'<polygon points="{" ".join(pts)}" fill="{color}"/><circle cx="60" cy="60" r="20" fill="#f8f0df"/><circle cx="60" cy="60" r="11" fill="{accent}"/>'
    if name=='Төртқұлақ':
        return f'''<g fill="{color}"><path d="M53 53C28 51 21 33 31 20c8-10 23-5 20 7-2 7-9 9-14 5 3 10 15 12 23 2z"/><path d="M67 53C69 28 87 21 100 31c10 8 5 23-7 20-7-2-9-9-5-14-10 3-12 15-2 23z"/><path d="M67 67c25 2 32 20 22 33-8 10-23 5-20-7 2-7 9-9 14-5-3-10-15-12-23-2z"/><path d="M53 67c-2 25-20 32-33 22-10-8-5-23 7-20 7 2 9 9 5 14 10-3 12-15 2-23z"/></g><circle cx="60" cy="60" r="10" fill="{accent}"/>'''
    return f'''<g fill="{color}"><path d="M18 36c18-23 35-20 42 1 7-21 24-24 42-1-21-4-24 13-15 24-9 11-6 28 15 24-18 23-35 20-42-1-7 21-24 24-42 1 21 4 24-13 15-24 9-11 6-28-15-24z"/></g><circle cx="60" cy="60" r="12" fill="{accent}"/>'''

def tile_svg(name,color,accent='#0d5e73',w=120,h=120):return f'<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">{motif_core(name,color,accent)}</svg>'

def composition_svg(g,w=160,h=160):
    colors=PALETTES[g['palette']];bg,main,accent=colors[0],colors[1],colors[2]
    core=motif_core(g['motif'],main,accent);n=max(4,min(int(g['repeats']),12));parts=[]
    if g['layout']=='Розетка':
        for i in range(4):parts.append(f'<g transform="translate({w/2-42},{h/2-42}) rotate({i*90+g["rotation"]} 42 42) scale(.70)">{core}</g>')
    elif g['layout']=='Бордюр':
        for i in range(min(n,5)):
            x=(i+.5)*w/min(n,5)-36;parts.append(f'<g transform="translate({x},{h/2-36}) scale(.60)">{core}</g>')
    elif g['layout']=='Сетка':
        for r in range(2):
            for c in range(2):parts.append(f'<g transform="translate({c*w/2+12},{r*h/2+12}) scale(.55)">{core}</g>')
    else:parts.append(f'<g transform="translate({w/2-60},{h/2-60}) rotate({g["rotation"]} 60 60) scale(1.0)">{core}</g>')
    return f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" rx="16" fill="{bg}"/>{"".join(parts)}</svg>'

def full_design_svg(g,w=1000,h=650):
    colors=PALETTES[g['palette']];bg,main,accent=colors[0],colors[1],colors[2];core=motif_core(g['motif'],main,accent);parts=[]
    n=max(4,min(int(g['repeats']),12))
    if g['layout']=='Розетка':
        for i in range(n):
            a=2*math.pi*i/n;R=min(w,h)*.29;x=w/2+R*math.cos(a)-60;y=h/2+R*math.sin(a)-60
            parts.append(f'<g transform="translate({x},{y}) rotate({math.degrees(a)+g["rotation"]} 60 60) scale({g["scale"]*.72})">{core}</g>')
    elif g['layout']=='Бордюр':
        for i in range(n):
            x=(i+.5)*w/n-60;parts.append(f'<g transform="translate({x},{h/2-60}) scale({g["scale"]*.75})">{core}</g>')
    elif g['layout']=='Сетка':
        cols=4;rows=max(2,math.ceil(n/cols));k=0
        for r in range(rows):
            for c in range(cols):
                if k>=n:break
                x=(c+.5)*w/cols-60;y=(r+.5)*h/rows-60;parts.append(f'<g transform="translate({x},{y}) scale({g["scale"]*.66})">{core}</g>');k+=1
    else:parts.append(f'<g transform="translate({w/2-60},{h/2-60}) rotate({g["rotation"]} 60 60) scale({g["scale"]*2.4})">{core}</g>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="{bg}"/><rect x="28" y="28" width="{w-56}" height="{h-56}" rx="30" fill="none" stroke="{accent}" opacity=".26" stroke-width="4"/>{"".join(parts)}</svg>'

def png_bytes(g,w=1000,h=650):
    # raster fallback drawing used only for quick download
    img=Image.new('RGB',(w,h),PALETTES[g['palette']][0]);d=ImageDraw.Draw(img);col=PALETTES[g['palette']][1]
    n=max(4,min(int(g['repeats']),12));cx,cy=w//2,h//2
    for i in range(n):
        a=2*math.pi*i/n;R=min(w,h)*.30;x=cx+R*math.cos(a);y=cy+R*math.sin(a);r=38
        d.ellipse((x-r,y-r,x+r,y+r),outline=col,width=8);d.arc((x-r*1.5,y-r*1.5,x+r*1.5,y+r*1.5),180,520,fill=col,width=8)
    out=io.BytesIO();img.save(out,'PNG');return out.getvalue()

# ---------- session ----------
for k,v in {'user':None,'guest':False,'population':[],'generation':0,'selected':[],'final_genome':None,'nav':'Дизайн-студия','motif':'Қошқар мүйіз','product':'Упаковка','style':'Современный','palette':'Qazaq Red','layout':'Розетка','mutation':.15,'pop_size':12}.items():
    if k not in st.session_state:st.session_state[k]=v

# ---------- auth ----------
def auth_screen():
    st.markdown('''<div class="og-auth-wrap"><div class="og-auth-card"><div style="font-family:Georgia,serif;font-size:38px;font-weight:900">ORNAMENTAL GENOME AI</div><div style="letter-spacing:.22em;margin-top:4px;color:#9b6e27">KAZAKH CREATIVE LAB</div><p style="font-size:17px">Эволюционная дизайн-платформа с персональным ИИ-профилем.</p></div></div>''',unsafe_allow_html=True)
    c0,c1,c2,c3=st.columns([1.5,1.3,1.3,1.5])
    with c1:
        st.subheader('Войти');u=st.text_input('Логин',key='lu');p=st.text_input('Пароль',type='password',key='lp')
        if st.button('Войти',use_container_width=True):
            row=login_user(u,p)
            if row:st.session_state.user=row;st.rerun()
            else:st.error('Неверный логин или пароль')
        if st.button('Попробовать как гость',use_container_width=True):st.session_state.guest=True;st.rerun()
    with c2:
        st.subheader('Регистрация');d=st.text_input('Имя',key='rd');u=st.text_input('Логин',key='ru');p=st.text_input('Пароль',type='password',key='rp')
        if st.button('Создать аккаунт',use_container_width=True):
            ok,msg=register_user(u,d,p);(st.success if ok else st.error)(msg)

if not st.session_state.user and not st.session_state.guest:
    auth_screen();st.stop()

user=st.session_state.user;uid=None if st.session_state.guest else int(user['id']);display='Гость' if st.session_state.guest else user['display_name']
model,nlearn=(None,0) if uid is None else personal_model(uid)

# top chrome
st.markdown(f'''<div class="og-top"><div class="og-brand"><div class="og-logo"><span>✦</span></div><div><b>ORNAMENTAL<br>GENOME AI</b><small>KAZAKH CREATIVE LAB</small></div></div><div class="og-nav"><span class="active">🎨 Дизайн-студия</span><span>🧬 Эволюция</span><span>▣ Библиотека</span><span>▢ Мои дизайны</span><span>▥ ИИ-профиль</span><span>⚗ Исследование</span></div><div class="og-user">◉ {display}⌄</div></div>''',unsafe_allow_html=True)

# navigation as working Streamlit control
nav_cols=st.columns([.18,.64,.18])
with nav_cols[1]:
    nav=st.radio('Раздел', ['Дизайн-студия','Эволюция','Библиотека','Мои дизайны','ИИ-профиль','Исследование'], horizontal=True, label_visibility='collapsed', key='nav')

# =========================================================
# MAIN DESIGN STUDIO — closest to supplied screenshot
# =========================================================
if nav=='Дизайн-студия':
    left,center,right=st.columns([.225,.58,.195],gap='small')
    with left:
        st.markdown('<div class="og-section-title"><span class="og-step">1</span>Выберите мотив</div>',unsafe_allow_html=True)
        # visual library grid
        cards=[]
        for name,(cat,col) in MOTIFS.items():
            active=' active' if name==st.session_state.motif else ''
            cards.append(f'<div class="og-motif-card{active}">{tile_svg(name,col)}<b>{name}</b></div>')
        st.markdown('<div class="og-motif-grid">'+''.join(cards)+'</div>',unsafe_allow_html=True)
        motif=st.selectbox('Мотив',list(MOTIFS),index=list(MOTIFS).index(st.session_state.motif),label_visibility='collapsed')
        st.session_state.motif=motif

        st.markdown('<div class="og-section-title"><span class="og-step">2</span>Выберите продукт</div>',unsafe_allow_html=True)
        icons={'Логотип':'◈','Упаковка':'▣','Постер':'▤','Текстиль':'▧','Сувенир':'♢','Соцсети':'▦'}
        st.markdown('<div class="og-product-grid">'+''.join([f'<div class="og-product{" active" if p==st.session_state.product else ""}"><span class="og-icon">{icons[p]}</span>{p}</div>' for p in PRODUCTS])+'</div>',unsafe_allow_html=True)
        product=st.selectbox('Продукт',PRODUCTS,index=PRODUCTS.index(st.session_state.product),label_visibility='collapsed');st.session_state.product=product

        st.markdown('<div class="og-section-title"><span class="og-step">3</span>Стиль и цветовая палитра</div>',unsafe_allow_html=True)
        style=st.segmented_control('Стиль',STYLES,default=st.session_state.style,label_visibility='collapsed');st.session_state.style=style or st.session_state.style
        palette=st.selectbox('Палитра',list(PALETTES),index=list(PALETTES).index(st.session_state.palette));st.session_state.palette=palette
        sw=''.join([f'<span class="og-swatch" style="background:{c}"></span>' for c in PALETTES[palette]])
        st.markdown(f'<div class="og-swatches">{sw}<span class="og-swatch" style="display:grid;place-items:center;background:#08384a">＋</span></div>',unsafe_allow_html=True)
        st.write('')
        create=st.button('🚀 СОЗДАТЬ ПОКОЛЕНИЕ',type='primary',use_container_width=True)
        if create:
            prog=st.progress(0,text='Создаём первое поколение...')
            for pct in [12,28,46,63,81,100]:time.sleep(.08);prog.progress(pct,text='Скрещивание признаков и построение композиции...')
            st.session_state.population=[random_genome(motif,st.session_state.style,st.session_state.layout,palette) for _ in range(st.session_state.pop_size)]
            st.session_state.generation=1;st.session_state.selected=[];st.session_state.final_genome=None;prog.empty();st.rerun()

    with center:
        st.markdown('''<div class="og-hero"><h1>Эволюция казахского орнамента</h1><p>ИИ изучает ваш дизайн-вкус — вы создаёте современные композиции</p><div class="motto">Дәстүр<br>Жаңашылдық<br>Болашақ</div></div>''',unsafe_allow_html=True)
        pop=st.session_state.population
        if pop and len(pop)>=2:a,b=pop[0],pop[1]
        else:a=random_genome(motif,st.session_state.style,'Розетка',palette);b=random_genome(motif,st.session_state.style,'Бордюр',palette)
        child=mutate(crossover(a,b),st.session_state.mutation)
        st.markdown(f'''<div class="og-main-card"><div class="og-evo-title">Процесс эволюции</div><div class="og-evo-row"><div class="og-stage"><small>Родитель 1</small>{tile_svg(a['motif'],PALETTES[a['palette']][1],PALETTES[a['palette']][2])}</div><div class="og-arrow">×</div><div class="og-stage"><small>Родитель 2</small>{tile_svg(b['motif'],PALETTES[b['palette']][2],PALETTES[b['palette']][1])}</div><div class="og-arrow">→</div><div class="og-stage"><small>Скрещивание</small>{composition_svg(child,120,120)}</div><div class="og-arrow">→</div><div class="og-stage"><small>Мутация</small>{tile_svg(child['motif'],'#9d9b91',PALETTES[child['palette']][1])}</div><div class="og-arrow">→</div><div class="og-stage"><small>Новая композиция</small>{composition_svg(child,120,120)}</div></div><div class="og-progress-bg"><div class="og-progress-fill"></div></div><div style="font-size:12px;margin-top:6px;color:#1c6072">Создание нового поколения… <b style="float:right">75%</b></div></div>''',unsafe_allow_html=True)
        st.write('')
        if not pop:
            pop=[random_genome(motif,st.session_state.style,st.session_state.layout,palette) for _ in range(12)]
        cards=[]
        ranked=sorted([(total_score(g,model)[0],i,g) for i,g in enumerate(pop)],reverse=True)
        for rank,(score,i,g) in enumerate(ranked[:12],1):
            heart='♥' if i in st.session_state.selected else '♡'
            cards.append(f'<div class="og-design"><div class="art">{composition_svg(g,150,150)}</div><div class="meta"><div><b>A{i+1:02d}</b><br><small>{score:.2f}</small></div><span class="og-heart">{heart}</span></div></div>')
        st.markdown(f'''<div class="og-main-card"><div class="og-gen-head"><h3>Поколение {max(1,st.session_state.generation)} <span style="font-size:12px;font-weight:500">12 вариантов</span></h3><div class="sort">Сортировка: Лучшие⌄ &nbsp;▦</div></div><div class="og-grid">{"".join(cards)}</div></div>''',unsafe_allow_html=True)
        st.caption('Выберите понравившиеся варианты ниже — они станут «родителями» следующего поколения.')
        choice_cols=st.columns(6)
        for j,(score,i,g) in enumerate(ranked[:12]):
            with choice_cols[j%6]:
                if st.button(('✅ ' if i in st.session_state.selected else '♡ ')+f'A{i+1:02d}',key=f'sel_{st.session_state.generation}_{i}',use_container_width=True):
                    if i in st.session_state.selected:st.session_state.selected.remove(i)
                    else:
                        st.session_state.selected.append(i)
                        if uid is not None:save_rating(uid,g,1,1.0)
                    st.rerun()
        bc1,bc2=st.columns([1,1])
        with bc1:
            if st.button('🧬 Следующее поколение',use_container_width=True):
                chosen=[pop[i] for i in st.session_state.selected if i<len(pop)]
                if len(chosen)<2:st.warning('Сначала выберите минимум 2 варианта.')
                else:
                    ph=st.empty();bar=st.progress(0)
                    for p in range(0,101,20):ph.info(f'Эволюция поколения {st.session_state.generation+1}: crossover → mutation → rendering');bar.progress(p);time.sleep(.09)
                    new=[]
                    while len(new)<st.session_state.pop_size:
                        pa,pb=random.sample(chosen,2);new.append(mutate(crossover(pa,pb),st.session_state.mutation))
                    st.session_state.population=new;st.session_state.generation+=1;st.session_state.selected=[];bar.empty();ph.empty();st.rerun()
        with bc2:
            if st.button('🏆 Выбрать лучший дизайн',use_container_width=True):
                st.session_state.final_genome=max(pop,key=lambda g:total_score(g,model)[0]);st.rerun()

    with right:
        st.markdown('<div class="og-panel"><div class="og-r-title">Параметры эволюции</div></div>',unsafe_allow_html=True)
        st.session_state.pop_size=st.selectbox('Размер популяции',[8,12,16,20],index=[8,12,16,20].index(st.session_state.pop_size))
        gens=st.selectbox('Поколений',[3,5,7,10],index=1)
        st.session_state.mutation=st.select_slider('Мутация',options=[.05,.10,.15,.20,.25,.30],value=st.session_state.mutation)
        preserve=st.toggle('Сохранять стиль мотива',value=True)
        st.write('')
        cat,col=MOTIFS[motif]
        st.markdown(f'''<div class="og-panel"><div class="og-r-title">О мотиве⌄</div><div class="og-motif-info"><div class="og-info-thumb">{tile_svg(motif,col)}</div><div class="og-copy"><b style="font-size:15px">{motif}</b><br>{cat}. Авторская параметрическая интерпретация мотива для цифрового эксперимента.<div class="og-link">Больше информации →</div></div></div></div>''',unsafe_allow_html=True)
        st.write('')
        preview_g=st.session_state.final_genome or (pop[0] if pop else a)
        core=tile_svg(preview_g['motif'],'#f6e4c5','#d63a34')
        st.markdown(f'''<div class="og-panel"><div class="og-r-title">Применить на продукте⌄</div><div class="og-pack"><div class="og-box"><div class="og-box-strip">{core}</div><div class="og-box-text">QAZAQ<br><b>CHOCOLATE</b></div></div></div><div class="og-download">⬇ Скачать дизайн⌄</div><div class="og-formats"><span class="og-format">PNG</span><span class="og-format">SVG</span><span class="og-format">PDF</span><span class="og-format">JPG</span></div></div>''',unsafe_allow_html=True)
        svg=full_design_svg(preview_g)
        st.download_button('Скачать SVG',svg,file_name='ornamental_genome.svg',mime='image/svg+xml',use_container_width=True)
        st.download_button('Скачать PNG',png_bytes(preview_g),file_name='ornamental_genome.png',mime='image/png',use_container_width=True)
        if uid is not None:
            name=st.text_input('Название дизайна','Qazaq Design')
            if st.button('💾 Сохранить в My Studio',use_container_width=True):save_design(uid,name,preview_g['motif'],preview_g,svg);st.success('Сохранено')

elif nav=='Эволюция':
    st.markdown('<div class="og-shell"><div class="og-hero"><h1>Evolution Lab</h1><p>Родители → скрещивание → мутация → новый вариант</p></div></div>',unsafe_allow_html=True)
    a=random_genome(st.session_state.motif,st.session_state.style,'Розетка',st.session_state.palette);b=random_genome(st.session_state.motif,st.session_state.style,'Бордюр',st.session_state.palette);c=mutate(crossover(a,b),st.session_state.mutation)
    cols=st.columns(3)
    for col,title,g in zip(cols,['Родитель A','Родитель B','Потомок'],[a,b,c]):
        with col:st.subheader(title);st.components.v1.html(full_design_svg(g,520,350),height=365)
    st.dataframe(pd.DataFrame([{'Ген':k,'A':a[k],'B':b[k],'Потомок':c[k]} for k in ['scale','rotation','repeats','spacing','density','curve','stroke','symmetry']]),use_container_width=True,hide_index=True)

elif nav=='Библиотека':
    st.markdown('<div class="og-shell"><div class="og-hero"><h1>Библиотека мотивов</h1><p>Источники, категории и цифровые векторизации</p></div></div>',unsafe_allow_html=True)
    cols=st.columns(3)
    for i,(name,(cat,col)) in enumerate(MOTIFS.items()):
        with cols[i%3]:
            st.markdown(f'<div class="og-main-card" style="margin-bottom:12px;text-align:center">{tile_svg(name,col)}<h3>{name}</h3><p>{cat}</p><small>В финальной версии: источник, страница/музейный объект, автор векторизации, допустимые трансформации.</small></div>',unsafe_allow_html=True)

elif nav=='Мои дизайны':
    st.markdown('<div class="og-shell"><div class="og-hero"><h1>Мои дизайны</h1><p>Персональная библиотека сохранённых работ</p></div></div>',unsafe_allow_html=True)
    if uid is None:st.warning('Войдите в аккаунт, чтобы сохранять библиотеку.')
    else:
        ds=get_designs(uid)
        if not ds:st.info('Пока нет сохранённых дизайнов.')
        else:
            cols=st.columns(3)
            for i,d in enumerate(ds):
                with cols[i%3]:st.components.v1.html(d['svg'],height=260);st.markdown(f"**{d['name']}** · {d['motif']}");st.download_button('SVG',d['svg'],file_name=f'OG_{d["id"]}.svg',mime='image/svg+xml',key=f'd_{d["id"]}')

elif nav=='ИИ-профиль':
    st.markdown('<div class="og-shell"><div class="og-hero"><h1>Мой AI Design DNA</h1><p>Персональная модель учится на ваших дизайнерских выборах</p></div></div>',unsafe_allow_html=True)
    if uid is None:st.warning('Для персонального ИИ нужен аккаунт.')
    else:
        st.metric('Обучающих выборов',nlearn)
        st.progress(min(nlearn/20,1.0),text='После 8 разнообразных выборов включается персональная модель.')
        st.info('ИИ не оценивает культурную «правильность». Он прогнозирует только ваши индивидуальные дизайнерские предпочтения.')
        pair=[random_genome(st.session_state.motif,'Минимал',random.choice(LAYOUTS),random.choice(list(PALETTES))),random_genome(st.session_state.motif,'Современный',random.choice(LAYOUTS),random.choice(list(PALETTES)))]
        cols=st.columns(2)
        for i,g in enumerate(pair):
            with cols[i]:st.components.v1.html(full_design_svg(g,520,350),height=365);a1,a2=st.columns(2)
            with a1:
                if st.button('♥ Нравится',key=f'ai_l{i}',use_container_width=True):save_rating(uid,g,1,1.0);st.rerun()
            with a2:
                if st.button('✕ Не моё',key=f'ai_d{i}',use_container_width=True):save_rating(uid,g,0,0.0);st.rerun()

else:
    st.markdown('<div class="og-shell"><div class="og-hero"><h1>Research Lab</h1><p>GA против случайного поиска при одинаковом вычислительном бюджете</p></div></div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns(3);mot=c1.selectbox('Мотив',list(MOTIFS));trials=c2.slider('Запусков',5,30,12);budget=c3.slider('Кандидатов',40,200,80,10)
    if st.button('▶ Провести эксперимент',type='primary'):
        data=[];bar=st.progress(0)
        for t in range(trials):
            rnd=max(total_score(random_genome(mot,'Современный','Розетка','Qazaq Red'))[0] for _ in range(budget))
            pop=[random_genome(mot,'Современный','Розетка','Qazaq Red') for _ in range(10)];evals=10
            while evals+10<=budget:
                pop=sorted(pop,key=lambda g:total_score(g)[0],reverse=True);parents=pop[:4];new=parents[:2]
                while len(new)<10:new.append(mutate(crossover(*random.sample(parents,2)),.15))
                pop=new;evals+=10
            ga=max(total_score(g)[0] for g in pop);data.append({'run':t+1,'GA':ga,'Random':rnd,'difference':ga-rnd});bar.progress((t+1)/trials)
        st.session_state.research_df=pd.DataFrame(data)
    if 'research_df' in st.session_state:
        df=st.session_state.research_df;c1,c2,c3=st.columns(3);c1.metric('Средний GA',f'{df.GA.mean():.3f}');c2.metric('Средний Random',f'{df.Random.mean():.3f}');c3.metric('Δ',f'{df.difference.mean():+.3f}');st.line_chart(df.set_index('run')[['GA','Random']]);st.dataframe(df,use_container_width=True,hide_index=True);st.download_button('CSV',df.to_csv(index=False).encode('utf-8-sig'),'ga_vs_random.csv','text/csv')

st.markdown('<div style="padding:14px 24px;border-top:1px solid rgba(255,255,255,.12);font-size:12px;color:#cad9dc;display:flex;justify-content:space-between"><span>✦ ORNAMENTAL GENOME AI · Kazakh Creative Lab</span><span>Традиция × Технологии × Творчество × Будущее</span><span>Made with ♥ in Kazakhstan</span></div>',unsafe_allow_html=True)
