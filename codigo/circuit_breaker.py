# circuit_breaker.py - Circuit Breaker UCI -> IA en nube (ventana COUNT_BASED 20, min 10 llamadas)
# Se usa un reloj virtual para que la demo sea determinista y no tarde minutos.
from collections import deque

class RelojVirtual:
    def __init__(self): self.t = 0.0
    def ahora(self): return self.t
    def dormir(self, s): self.t += s

class NubeSimulada:
    """Servidor de IA simulado: latencia (s) y bandera de caída."""
    def __init__(self): self.latencia, self.caida = 0.005, False
    def analizar(self, muestra, timeout, reloj):
        if self.caida:
            reloj.dormir(0.002); raise ConnectionError("WAN caída")
        if self.latencia > timeout:
            reloj.dormir(timeout); raise TimeoutError("timeout")
        reloj.dormir(self.latencia); return "diagnóstico-IA"

class CircuitBreaker:
    VENTANA, MIN_LLAMADAS, FALLOS, LENTAS = 20, 10, 0.20, 0.30
    LENTA_S, TIMEOUT_S, ESPERA_S, PRUEBAS = 0.5, 0.8, 15.0, 3
    def __init__(self, nube, reloj):
        self.nube, self.reloj = nube, reloj
        self.estado, self.ventana, self.t_apertura, self.pruebas = "CLOSED", deque(maxlen=self.VENTANA), 0.0, 0
    def _abrir(self): self.estado, self.t_apertura = "OPEN", self.reloj.ahora()
    def llamar(self, muestra):
        if self.estado == "OPEN":
            if self.reloj.ahora() - self.t_apertura >= self.ESPERA_S: self.estado, self.pruebas = "HALF_OPEN", 0
            else: return "fallback-local", "FALLBACK (circuito OPEN)", 0.0
        t0 = self.reloj.ahora()
        try: self.nube.analizar(muestra, self.TIMEOUT_S, self.reloj); ok = True
        except (TimeoutError, ConnectionError): ok = False
        dur = self.reloj.ahora() - t0
        lenta = dur > self.LENTA_S
        self.ventana.append((ok, lenta))
        if self.estado == "HALF_OPEN":
            self.pruebas += 1
            if (not ok) or lenta: self._abrir()
            elif self.pruebas == self.PRUEBAS: self.estado = "CLOSED"; self.ventana.clear()
        elif len(self.ventana) >= self.MIN_LLAMADAS:
            n = len(self.ventana)
            tf = sum(1 for o, _ in self.ventana if not o) / n
            tl = sum(1 for _, l in self.ventana if l) / n
            if tf >= self.FALLOS or tl >= self.LENTAS: self._abrir()
        return ("IA-nube" if ok else "fallback-local"), ("NUBE" if ok else "falló la nube"), dur

def escenario(titulo, pasos):
    reloj, nube = RelojVirtual(), NubeSimulada(); cb = CircuitBreaker(nube, reloj)
    print(f"\n=== {titulo} ===")
    n = 0
    for (cantidad, cfg) in pasos:
        for k, v in cfg.items(): setattr(nube, k, v)
        for _ in range(cantidad):
            n += 1; est_ant = cb.estado
            _, origen, dur = cb.llamar("ecg"); reloj.dormir(0.25)   # 4 consultas/s
            if cantidad <= 40 or est_ant != cb.estado or origen == "falló la nube" or n % 20 == 0:
                print(f"llamada {n:4d} | t={reloj.t:7.2f}s | {est_ant:9s}->{cb.estado:9s} | {origen:25s} | {dur*1000:6.1f} ms")
    return cb

if __name__ == "__main__":
    escenario("Caso 1: CLOSED -> OPEN por caída de la nube", [(30, {}), (10, {"caida": True})])
    escenario("Caso 2: OPEN -> HALF_OPEN (prueba falla) -> OPEN", [(30, {}), (6, {"caida": True}), (70, {})] if False else [(30, {}), (6, {"caida": True}), (62, {"caida": True})])
    escenario("Caso 3: recuperación HALF_OPEN -> CLOSED", [(30, {}), (6, {"caida": True}), (62, {"caida": False})])
    escenario("Caso 4: apertura por llamadas lentas (0,6 s)", [(12, {"latencia": 0.6})])
