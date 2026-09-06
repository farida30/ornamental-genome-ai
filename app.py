
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
from sklearn.ensemble import RandomForestRegressor
import random, math, time

st.set_page_config(page_title="Ornamental Genome AI", page_icon="🧬", layout="wide")

# -----------------------------
# ORNAMENTAL GENOME
# -----------------------------
GENE_NAMES = [
    "motif", "scale", "rotation", "repeats", "spacing",
    "symmetry", "radius", "density", "extra_probability"
]
MOTIFS = ["Қошқар мүйіз", "Тұмарша", "Геометриялық"]
SYMMETRIES = ["Линейная", "Зеркальная", "Центральная", "Радиальная"]

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def random_genome():
    return {
        "motif": random.randrange(len(MOTIFS)),
        "scale": random.uniform(0.45, 1.25),
        "rotation": random.uniform(0, 360),
        "repeats": random.randint(4, 16),
        "spacing": random.uniform(0.55, 1.8),
        "symmetry": random.randrange(len(SYMMETRIES)),
        "radius": random.uniform(1.0, 4.5),
        "density": random.uniform(0.35, 1.0),
        "extra_probability": random.uniform(0, 0.65)
    }

def repair(g):
    g["motif"] = int(clamp(round(g["motif"]), 0, len(MOTIFS)-1))
    g["scale"] = clamp(float(g["scale"]), 0.25, 1.6)
    g["rotation"] = float(g["rotation"]) % 360
    g["repeats"] = int(clamp(round(g["repeats"]), 3, 24))
    g["spacing"] = clamp(float(g["spacing"]), 0.35, 2.4)
    g["symmetry"] = int(clamp(round(g["symmetry"]), 0, len(SYMMETRIES)-1))
    g["radius"] = clamp(float(g["radius"]), 0.8, 5.0)
    g["density"] = clamp(float(g["density"]), 0.2, 1.0)
    g["extra_probability"] = clamp(float(g["extra_probability"]), 0, 0.9)
    return g

def vector(g):
    return np.array([g[k] for k in GENE_NAMES], dtype=float)

# -----------------------------
# FITNESS / RULE-BASED AI
# -----------------------------
def metrics(g):
    # Symmetry quality: the selected symmetry and compatible repeat count.
    if g["symmetry"] == 0:
        symmetry = 0.55 + 0.20 * (1 - abs(g["rotation"] % 90 - 45) / 45)
    elif g["symmetry"] == 1:
        symmetry = 1 - min(abs((g["rotation"] % 180) - 90) / 180, 0.45)
    elif g["symmetry"] == 2:
        symmetry = 0.72 + 0.28 * (1 if g["repeats"] % 2 == 0 else 0.45)
    else:
        divisors = [4, 6, 8, 12, 16]
        d = min(abs(g["repeats"] - x) for x in divisors)
        symmetry = clamp(1 - d / 8, 0, 1)

    # Diversity: medium probability of extra elements + moderate scale variation.
    diversity = 1 - abs(g["extra_probability"] - 0.35) / 0.65
    diversity *= 1 - 0.25 * abs(g["repeats"] - 12) / 12
    diversity = clamp(diversity, 0, 1)

    # Composition: target filling zone.
    fill_proxy = (g["repeats"] * g["scale"] * g["density"]) / (12 * 0.9)
    composition = math.exp(-abs(fill_proxy - 1.0) * 1.35)
    composition *= math.exp(-abs(g["spacing"] - 1.1) * 0.65)
    composition = clamp(composition, 0, 1)

    # Intersection penalty: dense large motifs at small spacing are undesirable.
    crowd = (g["scale"] * g["density"] * g["repeats"]) / max(g["spacing"], 0.2)
    intersections = clamp(1 - max(0, crowd - 8) / 16, 0, 1)

    # Constraints / plausibility.
    constraints = 1.0
    if g["radius"] < 1.1 and g["repeats"] > 15:
        constraints *= 0.65
    if g["scale"] > 1.35 and g["spacing"] < 0.7:
        constraints *= 0.55

    return {
        "symmetry": float(clamp(symmetry, 0, 1)),
        "diversity": float(clamp(diversity, 0, 1)),
        "composition": float(clamp(composition, 0, 1)),
        "non_intersection": float(clamp(intersections, 0, 1)),
        "constraints": float(clamp(constraints, 0, 1))
    }

def rule_fitness(g, weights):
    m = metrics(g)
    return sum(weights[k] * m[k] for k in weights), m

def train_ai_if_possible():
    labels = st.session_state.get("labels", [])
    if len(labels) < 6:
        return None
    X = np.vstack([vector(item["genome"]) for item in labels])
    y = np.array([item["rating"] for item in labels], dtype=float)
    if len(np.unique(y)) < 2:
        return None
    model = RandomForestRegressor(
        n_estimators=120, random_state=42, min_samples_leaf=1
    )
    model.fit(X, y)
    return model

def ai_score(g, model):
    if model is None:
        return None
    return float(model.predict(vector(g).reshape(1, -1))[0] / 5.0)

def fitness(g, weights, ai_model=None, ai_weight=0.25):
    base, m = rule_fitness(g, weights)
    a = ai_score(g, ai_model)
    if a is None:
        return base, m, None
    return (1-ai_weight)*base + ai_weight*a, m, a

# -----------------------------
# GENETIC ALGORITHM
# -----------------------------
def tournament(pop, scores, k=3):
    ids = random.sample(range(len(pop)), k=min(k, len(pop)))
    return pop[max(ids, key=lambda i: scores[i])]

def crossover(a, b):
    c = {}
    for k in GENE_NAMES:
        if k in ["motif", "symmetry", "repeats"]:
            c[k] = a[k] if random.random() < 0.5 else b[k]
        else:
            alpha = random.random()
            c[k] = alpha*a[k] + (1-alpha)*b[k]
    return repair(c)

def mutate(g, p):
    g = dict(g)
    for k in GENE_NAMES:
        if random.random() < p:
            if k == "motif":
                g[k] = random.randrange(len(MOTIFS))
            elif k == "symmetry":
                g[k] = random.randrange(len(SYMMETRIES))
            elif k == "repeats":
                g[k] += random.choice([-3,-2,-1,1,2,3])
            elif k == "rotation":
                g[k] += random.uniform(-55, 55)
            elif k == "scale":
                g[k] += random.uniform(-0.22, 0.22)
            elif k == "spacing":
                g[k] += random.uniform(-0.35, 0.35)
            elif k == "radius":
                g[k] += random.uniform(-0.8, 0.8)
            else:
                g[k] += random.uniform(-0.20, 0.20)
    return repair(g)

def evolve(pop_size, generations, mutation_rate, weights, ai_model, ai_weight):
    pop = [random_genome() for _ in range(pop_size)]
    history = []
    snapshots = []

    for gen in range(generations + 1):
        evaluated = [fitness(g, weights, ai_model, ai_weight) for g in pop]
        scores = np.array([x[0] for x in evaluated])
        order = np.argsort(scores)[::-1]
        best = dict(pop[order[0]])
        history.append({
            "generation": gen,
            "best": float(scores.max()),
            "mean": float(scores.mean()),
            "min": float(scores.min())
        })
        if gen in {0, generations//2, generations}:
            snapshots.append((gen, best, float(scores.max())))

        if gen == generations:
            break

        elites = [dict(pop[i]) for i in order[:max(2, pop_size//10)]]
        new_pop = elites[:]
        while len(new_pop) < pop_size:
            p1 = tournament(pop, scores)
            p2 = tournament(pop, scores)
            child = crossover(p1, p2)
            child = mutate(child, mutation_rate)
            new_pop.append(child)
        pop = new_pop[:pop_size]

    final_scores = [fitness(g, weights, ai_model, ai_weight)[0] for g in pop]
    best_idx = int(np.argmax(final_scores))
    return pop[best_idx], history, snapshots, pop, final_scores

# -----------------------------
# DRAWING ENGINE
# -----------------------------
def motif_points(name, scale=1.0):
    t = np.linspace(0, 2*np.pi, 180)
    if name == "Қошқар мүйіз":
        # Stylized ram-horn spiral curve.
        r = scale*(0.12 + 0.12*t)
        x = r*np.cos(t)
        y = r*np.sin(t)
        return x, y
    if name == "Тұмарша":
        x = np.array([0, 0.55, 0, -0.55, 0])*scale
        y = np.array([0.7, 0, -0.7, 0, 0.7])*scale
        return x, y
    # geometric motif
    x = np.array([-0.5,0,0.5,0,-0.5])*scale
    y = np.array([0,0.5,0,-0.5,0])*scale
    return x, y

def transform(x, y, angle_deg, tx, ty, mirror=False):
    if mirror:
        x = -x
    a = np.deg2rad(angle_deg)
    xr = x*np.cos(a) - y*np.sin(a) + tx
    yr = x*np.sin(a) + y*np.cos(a) + ty
    return xr, yr

def draw_ornament(g, ax=None, title=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(6,6))
    else:
        fig = ax.figure

    name = MOTIFS[g["motif"]]
    n = g["repeats"]
    sym = g["symmetry"]
    x0, y0 = motif_points(name, g["scale"])

    # Placement strategy follows the genome's symmetry gene.
    if sym == 0:  # linear
        xs = np.linspace(-g["radius"], g["radius"], n)
        for i, x in enumerate(xs):
            y = 0.45*np.sin(i*0.8 + np.deg2rad(g["rotation"]))
            xr, yr = transform(x0, y0, g["rotation"] + i*8, x, y)
            ax.plot(xr, yr, linewidth=2)
    elif sym == 1:  # mirror
        half = max(2, n//2)
        xs = np.linspace(0.4, g["radius"], half)
        for i, x in enumerate(xs):
            ang = g["rotation"] + i*9
            for sign, mir in [(1,False),(-1,True)]:
                xr, yr = transform(x0, y0, ang, sign*x, 0.55*np.sin(i), mir)
                ax.plot(xr, yr, linewidth=2)
    elif sym == 2:  # central
        half = max(2, n//2)
        for i in range(half):
            theta = 2*np.pi*i/half
            x, y = g["radius"]*np.cos(theta), g["radius"]*np.sin(theta)
            xr, yr = transform(x0, y0, g["rotation"] + np.degrees(theta), x, y)
            ax.plot(xr, yr, linewidth=2)
            xr, yr = transform(x0, y0, g["rotation"] + np.degrees(theta)+180, -x, -y, True)
            ax.plot(xr, yr, linewidth=2)
    else:  # radial
        for i in range(n):
            theta = 2*np.pi*i/n
            r = g["radius"]*(0.55 + 0.45*g["density"])
            x, y = r*np.cos(theta), r*np.sin(theta)
            xr, yr = transform(x0, y0, g["rotation"] + np.degrees(theta), x, y)
            ax.plot(xr, yr, linewidth=2)

    # Optional secondary motif.
    if g["extra_probability"] > 0.20:
        small = g["scale"] * (0.25 + 0.55*g["extra_probability"])
        xs, ys = motif_points("Геометриялық", small)
        m = max(3, int(n*g["extra_probability"]))
        for i in range(m):
            theta = 2*np.pi*i/m
            r = max(0.35, g["radius"]*0.45)
            xr, yr = transform(xs, ys, g["rotation"]-np.degrees(theta),
                               r*np.cos(theta), r*np.sin(theta))
            ax.plot(xr, yr, linewidth=1.2)

    lim = g["radius"] + 2.2
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.axis("off")
    if title:
        ax.set_title(title)
    return fig

# -----------------------------
# UI
# -----------------------------
st.title("🧬 ORNAMENTAL GENOME AI")
st.caption("Эволюционная генерация новых орнаментальных композиций с элементами искусственного интеллекта")

if "labels" not in st.session_state:
    st.session_state.labels = []
if "gallery" not in st.session_state:
    st.session_state.gallery = []

with st.sidebar:
    st.header("Параметры эксперимента")
    pop_size = st.slider("Размер популяции", 20, 200, 60, 10)
    generations = st.slider("Количество поколений", 5, 120, 35, 5)
    mutation_rate = st.slider("Вероятность мутации", 0.01, 0.50, 0.12, 0.01)
    ai_weight = st.slider("Вес ИИ-оценки", 0.0, 0.60, 0.25, 0.05)

    st.subheader("Веса функции fitness")
    wS = st.slider("Симметрия", 0.0, 1.0, 0.30, 0.05)
    wD = st.slider("Разнообразие", 0.0, 1.0, 0.15, 0.05)
    wC = st.slider("Композиция", 0.0, 1.0, 0.25, 0.05)
    wP = st.slider("Отсутствие пересечений", 0.0, 1.0, 0.20, 0.05)
    wR = st.slider("Ограничения", 0.0, 1.0, 0.10, 0.05)

weights_raw = np.array([wS,wD,wC,wP,wR], dtype=float)
if weights_raw.sum() == 0:
    weights_raw[0] = 1
weights_raw /= weights_raw.sum()
weights = dict(zip(
    ["symmetry","diversity","composition","non_intersection","constraints"],
    weights_raw
))

tabs = st.tabs(["🚀 Эволюция", "🎨 Ручной геном", "🤖 Обучение ИИ", "📊 Исследование", "📚 О проекте"])

# TAB 1
with tabs[0]:
    ai_model = train_ai_if_possible()
    st.write("Нажмите кнопку, чтобы создать популяцию и провести эволюционный поиск.")
    if ai_model is None:
        st.info("ИИ-модель пока не обучена: используется математическая многокритериальная оценка. После 6+ пользовательских оценок включится обучаемый модуль Random Forest.")

    if st.button("Запустить эволюцию", type="primary"):
        t0 = time.time()
        best, history, snapshots, final_pop, final_scores = evolve(
            pop_size, generations, mutation_rate, weights, ai_model, ai_weight
        )
        elapsed = time.time() - t0
        st.session_state.last_run = {
            "best": best, "history": history, "snapshots": snapshots,
            "final_pop": final_pop, "final_scores": final_scores,
            "elapsed": elapsed
        }

    if "last_run" in st.session_state:
        run = st.session_state.last_run
        best = run["best"]
        score, m, a = fitness(best, weights, train_ai_if_possible(), ai_weight)

        c1, c2 = st.columns([1.15, 1])
        with c1:
            fig = draw_ornament(best, title=f"Лучшая композиция | Fitness={score:.3f}")
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        with c2:
            st.subheader("Орнаментальный геном")
            table = pd.DataFrame({
                "Ген": GENE_NAMES,
                "Значение": [
                    MOTIFS[best["motif"]], round(best["scale"],3), round(best["rotation"],1),
                    best["repeats"], round(best["spacing"],3), SYMMETRIES[best["symmetry"]],
                    round(best["radius"],3), round(best["density"],3), round(best["extra_probability"],3)
                ]
            })
            st.dataframe(table, use_container_width=True, hide_index=True)
            st.metric("Время эксперимента", f"{run['elapsed']:.2f} сек")
            if a is not None:
                st.metric("Прогноз ИИ", f"{a:.3f}")

        st.subheader("Динамика эволюции")
        h = pd.DataFrame(run["history"]).set_index("generation")
        st.line_chart(h[["best","mean","min"]])

        st.subheader("Поколения: как менялась композиция")
        cols = st.columns(len(run["snapshots"]))
        for col, (gen, genome, sc) in zip(cols, run["snapshots"]):
            with col:
                fig = draw_ornament(genome, title=f"Поколение {gen}\n{sc:.3f}")
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

        st.subheader("Дать экспертную оценку лучшей композиции")
        rating = st.slider("Оценка от 1 до 5", 1, 5, 4, key="best_rating")
        if st.button("Добавить оценку для обучения ИИ"):
            st.session_state.labels.append({"genome": dict(best), "rating": rating})
            st.success(f"Оценка сохранена. Всего примеров для обучения: {len(st.session_state.labels)}")

# TAB 2
with tabs[1]:
    st.subheader("Конструктор одного орнаментального генома")
    col1, col2, col3 = st.columns(3)
    with col1:
        motif = st.selectbox("Базовый мотив", MOTIFS)
        scale = st.slider("Масштаб", 0.25, 1.60, 0.8, 0.05)
        rotation = st.slider("Угол поворота", 0, 359, 0)
    with col2:
        repeats = st.slider("Количество повторов", 3, 24, 8)
        spacing = st.slider("Шаг / интервал", 0.35, 2.4, 1.1, 0.05)
        symmetry = st.selectbox("Тип симметрии", SYMMETRIES)
    with col3:
        radius = st.slider("Радиус размещения", 0.8, 5.0, 2.5, 0.1)
        density = st.slider("Плотность", 0.2, 1.0, 0.75, 0.05)
        extra = st.slider("Дополнительный элемент", 0.0, 0.9, 0.25, 0.05)

    g = {
        "motif": MOTIFS.index(motif), "scale": scale, "rotation": rotation,
        "repeats": repeats, "spacing": spacing, "symmetry": SYMMETRIES.index(symmetry),
        "radius": radius, "density": density, "extra_probability": extra
    }
    sc, mm, aa = fitness(g, weights, train_ai_if_possible(), ai_weight)
    fig = draw_ornament(g, title=f"Fitness = {sc:.3f}")
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.dataframe(pd.DataFrame([mm]), use_container_width=True)

# TAB 3
with tabs[2]:
    st.subheader("Обучаемый модуль ИИ на основе экспертной обратной связи")
    st.write(
        "Идея: пользователь оценивает созданные композиции по шкале 1–5. "
        "После накопления минимум 6 размеченных примеров Random Forest обучается "
        "предсказывать экспертную оценку по параметрам орнаментального генома."
    )
    st.metric("Размеченных примеров", len(st.session_state.labels))

    if st.button("Сгенерировать 6 вариантов для разметки"):
        st.session_state.gallery = [random_genome() for _ in range(6)]

    if st.session_state.gallery:
        cols = st.columns(3)
        for i, g in enumerate(st.session_state.gallery):
            with cols[i % 3]:
                fig = draw_ornament(g, title=f"Вариант {i+1}")
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
                r = st.slider("Оценка", 1, 5, 3, key=f"gallery_{i}")
                if st.button("Сохранить", key=f"save_{i}"):
                    st.session_state.labels.append({"genome": dict(g), "rating": r})
                    st.success("Сохранено")

    model = train_ai_if_possible()
    if model is not None:
        st.success("ИИ-модель обучена и может участвовать в fitness-функции.")
        importance = pd.DataFrame({
            "Ген": GENE_NAMES,
            "Важность": model.feature_importances_
        }).sort_values("Важность", ascending=False)
        st.bar_chart(importance.set_index("Ген"))
    else:
        st.warning("Для обучения требуется минимум 6 оценённых вариантов и хотя бы две разные оценки.")

# TAB 4
with tabs[3]:
    st.subheader("Сравнение случайной и эволюционной генерации")
    st.write("Этот раздел предназначен для получения фактических данных для главы 4 научной работы.")
    if st.button("Провести сравнительный эксперимент"):
        ai_model = train_ai_if_possible()
        random_pop = [random_genome() for _ in range(pop_size)]
        random_scores = [fitness(g, weights, ai_model, ai_weight)[0] for g in random_pop]
        best, history, snapshots, pop, scores = evolve(
            pop_size, generations, mutation_rate, weights, ai_model, ai_weight
        )
        results = pd.DataFrame({
            "Метод": ["Случайная генерация", "Эволюционная генерация"],
            "Средний fitness": [np.mean(random_scores), np.mean(scores)],
            "Лучший fitness": [np.max(random_scores), np.max(scores)],
            "Поколений": [0, generations],
            "Размер популяции": [pop_size, pop_size]
        })
        st.dataframe(results, use_container_width=True, hide_index=True)
        st.bar_chart(results.set_index("Метод")[["Средний fitness","Лучший fitness"]])

        csv = results.to_csv(index=False).encode("utf-8-sig")
        st.download_button("Скачать таблицу CSV", csv, "experiment_results.csv", "text/csv")

# TAB 5
with tabs[4]:
    st.markdown("""
### Научная логика приложения

**1. Геном.** Каждая композиция кодируется девятью параметрами:
тип мотива, масштаб, угол, число повторов, интервал, тип симметрии,
радиус, плотность и вероятность дополнительного элемента.

**2. Генетический алгоритм.** Создаётся популяция вариантов. Для каждого
варианта вычисляется fitness. Затем применяются турнирный отбор,
равномерно-арифметическое скрещивание, мутация и элитизм.

**3. Многокритериальная функция.**
`F = w1·S + w2·D + w3·C + w4·P + w5·R`

где S — симметрия, D — разнообразие, C — композиционная заполненность,
P — отсутствие нежелательной перегруженности/пересечений, R — соблюдение
ограничений.

**4. Реальный элемент машинного обучения.** После экспертной разметки
композиций обучается `RandomForestRegressor`, который прогнозирует
человеческую оценку и может включаться в функцию fitness.

**5. Исследовательский результат.** Приложение позволяет получать
таблицы, графики, промежуточные поколения и сравнение случайного поиска
с эволюционным. Это делает программу не просто генератором картинок,
а инструментом вычислительного эксперимента.
""")
