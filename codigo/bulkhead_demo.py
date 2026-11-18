# bulkhead_demo.py - Pools de hilos independientes: la IA saturada no afecta a las alertas
import time, threading
from concurrent.futures import ThreadPoolExecutor
pool_alertas = ThreadPoolExecutor(max_workers=16, thread_name_prefix="uci-alerta")
pool_ia = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ia-nube")
cupo_ia = threading.BoundedSemaphore(4 + 20)
def fallback_local(m): return "fallback"
def llamar_ia(m): time.sleep(2.0); return "ia"          # nube simulada con 2 s de latencia
def enviar_a_ia(m):
    if not cupo_ia.acquire(blocking=False): return fallback_local(m)
    fut = pool_ia.submit(llamar_ia, m); fut.add_done_callback(lambda _: cupo_ia.release()); return fut
res = [enviar_a_ia(i) for i in range(40)]
rechazadas = sum(1 for r in res if r == "fallback")
print(f"Peticiones a IA: 40 | aceptadas: {40-rechazadas} (4 ejecutando + 20 en cola) | rechazadas con fallback inmediato: {rechazadas}")
t0 = time.perf_counter()
futs = [pool_alertas.submit(lambda i=i: i) for i in range(5)]
[f.result() for f in futs]
print(f"5 alertas críticas atendidas con la IA saturada en {(time.perf_counter()-t0)*1000:.1f} ms")
for r in res:
    if hasattr(r, "cancel"): r.cancel()
pool_ia.shutdown(wait=False, cancel_futures=True)
