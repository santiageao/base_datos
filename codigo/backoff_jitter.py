# backoff_jitter.py - Sesión 12, Ejercicio 3: backoff exponencial con jitter vs Thundering Herd
import random
from collections import Counter
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
T_BASE, T_MAX, JITTER, N, C = 1.0, 30.0, 0.5, 10_000, 2_000
random.seed(42)
def t_wait(i, jitter=True): return min(T_MAX, T_BASE * 2 ** i) + (random.uniform(0, JITTER) if jitter else 0.0)
def t_full(i): return random.uniform(0, min(T_MAX, T_BASE * 2 ** i))
def llegadas(v, i=1):
    f = {"sin": lambda: t_wait(i, False), "jitter": lambda: t_wait(i, True), "full": lambda: t_full(i)}[v]
    return [int(f() * 1000) for _ in range(N)]
def analizar(titulo, ts):
    pico = max(Counter(ts).values()); por_s = Counter(t // 1000 for t in ts)
    tps = max(por_s.values()); seg = sum(1 for v in por_s.values() if v > C)
    print(f"{titulo:42s} pico={pico:6d}/ms  carga máx={tps:6d} TPS  s>{C}TPS={seg}  {'SATURADO' if tps > C else 'OK'}")
    return dict(titulo=titulo, t=ts, estado="SATURADO" if tps > C else "OK")
r = [analizar("Sin jitter (reintento 1)", llegadas("sin")),
     analizar("Jitter fijo U(0;0,5 s) (reintento 1)", llegadas("jitter")),
     analizar("Full Jitter reintento 1 (ventana 2 s)", llegadas("full", 1)),
     analizar("Full Jitter reintento 2 (ventana 4 s)", llegadas("full", 2)),
     analizar("Full Jitter reintento 3 (ventana 8 s)", llegadas("full", 3)),
     analizar("Full Jitter reintento 4 (ventana 16 s)", llegadas("full", 4))]
print(f"N/W jitter fijo = {N/JITTER:.0f} TPS | N/W full jitter 1 = {N/2:.0f} TPS | W_min = N/C = {N/C:.1f} s")
print(f"Buses: 500/10 = {500/10:.0f} TPS | Token Bucket AgroSugar 1500 -> libres {C-1500} TPS para MetroMIO")
paneles = [(r[0], (1.5, 2.5)), (r[1], (1.9, 2.6)), (r[2], (0, 2)), (r[4], (0, 8))]
fig, ejes = plt.subplots(2, 2, figsize=(11, 7.5), sharey=True)
for ax, (x, lim) in zip(ejes.flat, paneles):
    b = Counter(t // 50 for t in x["t"])
    ax.bar([k*0.05 for k in b], [v/0.05 for v in b.values()], width=0.05, align="edge", color="#c0392b" if x["estado"]=="SATURADO" else "#27ae60")
    ax.axhline(C, ls="--", color="#1f4e9c", label=f"Capacidad gateway ({C} TPS)")
    ax.set_yscale("log"); ax.set_xlim(*lim); ax.set_title(x["titulo"], fontsize=9); ax.set_xlabel("Tiempo desde la falla (s)"); ax.grid(alpha=.3)
for ax in ejes[:, 0]: ax.set_ylabel("Carga (TPS, escala log)")
ejes[0, 0].legend(fontsize=8, loc="lower left")
fig.suptitle("Ejercicio 3 - Llegadas de 10.000 sensores AgroSugar (bins de 50 ms)"); plt.tight_layout(); plt.savefig("grafica_backoff.png", dpi=130)
