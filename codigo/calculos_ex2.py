# calculos_ex2.py - Error budget, serie vs paralelo y Ley de Little
U = 1 - 0.99999
for nombre, minutos in [("Año", 525600), ("Mes (30 d)", 43200), ("Semana", 10080), ("Día", 1440)]:
    m = minutos * U; print(f"{nombre:10s}: {minutos:7d} min x 1e-5 = {m:.4f} min = {m*60:.2f} s")
AL, AW, AC, AF = 0.999995, 0.999, 0.9995, 0.9999
Ar = AW * AC; As = AL * Ar
print(f"\nA_remota = {Ar:.7f}   A_serie = {As:.6f}   caída = {(1-As)*525600:.1f} min/año = {(1-As)*525600/60:.2f} h/año")
Af = 1 - (1 - Ar) * (1 - AF); At = AL * Af
print(f"A_func = {Af:.8f}   A_total = {At:.7f}   caída = {(1-At)*525600:.2f} min/año")
print(f"Verificación AL=0,99999: {0.99999*Af:.8f}  ->  {'cumple' if 0.99999*Af >= 0.99999 else 'NO cumple'}")
lam = 100
print(f"\nLey de Little: sin CB L = {lam}x5 = {lam*5} hilos ; OPEN L = {lam}x0,00005 = {lam*0.00005} hilos")
