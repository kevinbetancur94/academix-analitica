"""Academix · API Spring Boot -> notebook (pandas/matplotlib) -> reporte HTML -> front React.

Uso:
  python generar_reporte.py                      # API en localhost:8080, respaldo a CSV
  python generar_reporte.py --api https://proyecto-academix.onrender.com/api
  python generar_reporte.py --fuente csv         # solo datos de ejemplo
  python generar_reporte.py --front ../Academix-Front-Final   # publica en public/reportes/
Requiere: pip install pandas matplotlib requests ipykernel nbformat nbclient
"""
import argparse, base64, html, os, shutil, subprocess, sys
from pathlib import Path
import numpy as np, pandas as pd, requests

ap = argparse.ArgumentParser()
ap.add_argument("--fuente", default="api", choices=["api", "csv"])
ap.add_argument("--api", default="http://localhost:8080/api")
ap.add_argument("--salida", default="reporte")
ap.add_argument("--front", help="carpeta raíz del front React; copia el reporte a public/reportes/")
ap.add_argument("--sin-notebook", action="store_true", help="no re-ejecutar el notebook (usa las gráficas existentes)")
a = ap.parse_args()
AQUI = Path(__file__).parent

# 1) Datos: API real, con respaldo a los CSV de ejemplo
fuente = a.fuente
if fuente == "api":
    try:
        t, c = (pd.DataFrame(requests.get(f"{a.api}/{r}", timeout=90).json() ) for r in ("tareas", "calificaciones"))
        if t.empty or c.empty: raise ValueError("la API respondió sin datos")
    except Exception as e:
        print(f"API no disponible ({e}); se usan los CSV.")
        fuente = "csv"
if fuente == "csv":
    t, c = pd.read_csv(AQUI / "datos/tareas.csv"), pd.read_csv(AQUI / "datos/calificaciones.csv")
etq_fuente = f"API Academix ({a.api})" if fuente == "api" else "CSV de ejemplo (datos/)"

# 2) Notebook: regenera las gráficas con la misma fuente
if not a.sin_notebook:
    import nbformat
    from nbclient import NotebookClient
    os.environ["ACADEMIX_FUENTE"], os.environ["ACADEMIX_API"] = fuente, a.api   # el kernel los hereda
    ruta_nb = AQUI / "taller_academix.ipynb"
    nb = nbformat.read(ruta_nb, as_version=4)
    NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(AQUI)}}).execute()
    nbformat.write(nb, ruta_nb)

# 3) Métricas (mismas definiciones que el notebook)
HOY = pd.Timestamp.today().normalize()
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
em = lambda p: f"{MES[p.month-1]} {p.year}"
t["fecha"] = pd.to_datetime(t["fecha"]); t["mes"] = t.fecha.dt.to_period("M")
t["dia"] = t.fecha.dt.dayofweek.map(dict(enumerate(DIAS)))
t["estado"] = np.where(~t.estadoActivo.astype(bool), "Inactiva", np.where(t.fecha < HOY, "Fecha cumplida", "Por entregar"))
pm = t.groupby("mes").size().sort_index(); cons = t.materiaNombre.value_counts(); part = cons / cons.sum() * 100
prom = c.groupby("materiaNombre").promedio.mean().sort_values(); pg = c.promedio.mean()
pend = np.polyfit(range(len(pm)), pm.values, 1)[0]
tend = "creciente" if pend > .5 else "decreciente" if pend < -.5 else "estable"
dd = t.dia.value_counts().reindex(DIAS, fill_value=0).sort_values(ascending=False)
ma, mp = HOY.to_period("M"), HOY.to_period("M") - 1
va, vp = pm.get(ma, 0), pm.get(mp, 0)
var = (va - vp) / vp * 100 if vp else float("nan")
est = t.estado.value_counts(); estp = (est / est.sum() * 100).round(1)
fin = t.fecha.dt.dayofweek >= 5; cal = pd.date_range(t.fecha.min(), t.fecha.max())
d_fin = int((cal.dayofweek >= 5).sum()); d_sem = len(cal) - d_fin
top3 = cons.nlargest(3).index
ev = t[t.materiaNombre.isin(top3)].groupby(["mes", "materiaNombre"]).size().unstack(fill_value=0).reindex(pm.index, fill_value=0)
ind = pd.DataFrame({"tot": cons, "pen": t[t.estado == "Por entregar"].groupby("materiaNombre").size(), "nota": prom}).fillna(0)
med = ind.mean()
ind["al"] = (ind.tot > med.tot).astype(int) + (ind.pen > med.pen).astype(int) + (ind.nota < med.nota).astype(int)
ind = ind.sort_values(["al", "pen"], ascending=False); crit = ind.index[0]; fc = ind.loc[crit]
peor = prom.index[0]; repr_ = (c[c.materiaNombre == peor].promedio < 3).mean() * 100
sup = [m for m in prom.index[::-1] if prom[m] >= pg]; inf = [m for m in prom.index if prom[m] < pg]
n_al = ind[ind.al == ind.al.max()].index.tolist()
b3 = cons.nsmallest(3); top5 = cons.nlargest(5)
f1 = lambda x: f"{x:.1f}"
J = lambda xs: ", ".join(xs)
pico = "; ".join(f"{m}: pico {em(ev[m].idxmax())} ({ev[m].max()})" for m in top3)

B = [
("01", "Tendencias en el tiempo", [
 ("p01", "P1 · Tareas por mes", f"Tendencia {tend} ({pend:+.1f} tareas/mes). Máximo: {em(pm.idxmax())} ({pm.max()}). Mínimo: {em(pm.idxmin())} ({pm.min()}).", "Hay meses de mucha y poca carga. Los datos no explican la causa; hay que confirmarla con el calendario académico."),
 ("p02", "P2 · Entregas por día de la semana", f"{dd.index[0]} ({dd.iloc[0]}) y {dd.index[1]} ({dd.iloc[1]}) concentran el {f1(dd.head(2).sum()/dd.sum()*100)} % de las entregas.", "Las entregas se acumulan en pocos días; conviene revisar si eso satura a los estudiantes."),
 ("p03", "P3 · Mes actual vs. anterior", f"{em(mp)}: {vp} tareas · {em(ma)}: {va}. Variación: {var:+.1f} %." if vp else "No hay datos del mes anterior.", "Un cambio de pocos puntos porcentuales no es concluyente por sí solo.")]),
("02", "Participación y composición", [
 ("p07", "P7 · Participación por materia", f"{J(f'{m} {f1(part[m])} %' for m in part.index[:3])}: las tres suman {f1(part.head(3).sum())} %.", "Muestra qué materias dominan la carga total."),
 ("p08", "P8 · Estado de las tareas", " · ".join(f"{k} {estp[k]} % ({est[k]})" for k in est.index) + ".", "«Fecha cumplida» significa que la fecha ya pasó, no que el estudiante entregó. Mejora propuesta: enum <code>EstadoTarea</code> (PENDIENTE, ENTREGADA, CANCELADA).")]),
("03", "Promedios", [
 ("p13", "P13 · Nota promedio por materia", f"Promedio general {pg:.2f}. Por debajo: {J(f'{m} ({prom[m]:.2f})' for m in inf)}.", f"Superan el promedio: {J(sup)}.")]),
("04", "Máximos, mínimos y rankings", [
 ("p18", "P18 · Top 5 materias con más tareas", f"1.º {top5.index[0]} ({top5.iloc[0]}), 2.º {top5.index[1]} ({top5.iloc[1]}): {top5.iloc[0]-top5.iloc[1]} tareas más (+{f1((top5.iloc[0]/top5.iloc[1]-1)*100)} %).", "Diferencia entre los dos primeros lugares."),
 ("p19", "P19 · Las 3 materias con menos tareas", J(f"{m} ({v})" for m, v in b3.items()) + ".", f"Pregunta a investigar: ¿{b3.index[0]} tiene menos tareas porque se evalúa en clase o porque tiene menos horas semanales?"),
 ("p20", "P20 · Mes máximo y mínimo", f"{em(pm.idxmax())} ({pm.max()}) vs. {em(pm.idxmin())} ({pm.min()}): diferencia de {pm.max()-pm.min()} tareas, {pm.max()/pm.min():.1f} veces. Promedio mensual: {pm.mean():.0f}.", "Verificar si el mínimo coincide con vacaciones o con un mes incompleto.")]),
("08", "Comparaciones", [
 ("p39", "P39 · Entre semana vs. fin de semana", f"Entre semana {int((~fin).sum())} ({(~fin).sum()/d_sem:.2f} por día) · Fin de semana {int(fin.sum())} ({fin.sum()/d_fin:.2f} por día). El {f1(fin.mean()*100)} % cae en fin de semana.", "Se compara el promedio por día, no el total, porque hay 5 días entre semana y 2 de fin de semana. Posible mejora: advertir al docente si elige sábado o domingo."),
 ("p40", "P40 · Evolución del top 3", pico + ".", "Compara en qué meses concentra su carga cada materia.")]),
("09", "Reporte final", [
 ("p44", "P44 · Situación general", f"{len(t)} tareas · {int((t.estado=='Por entregar').sum())} por entregar · nota promedio {pg:.2f} · materia principal: {cons.idxmax()} ({cons.max()}, {f1(part.max())} %).", f"La materia con nota más baja es {peor} ({prom.iloc[0]:.2f})."),
 ("p45", "P45 · Tres hallazgos", f"1) {part.idxmax()} concentra el {f1(part.max())} % de las tareas. 2) {peor} tiene la nota más baja ({prom.iloc[0]:.2f}) y el {f1(repr_)} % de sus registros está bajo 3.0. 3) {em(pm.idxmax())} tuvo {pm.max()} tareas, {f1((pm.max()/pm.mean()-1)*100)} % sobre el promedio mensual.", "Recomendaciones: revisar la carga, programar refuerzo con seguimiento a acudientes y coordinar fechas en los meses pico."),
 ("p46", "P46 · Materia que requiere atención", f"{crit} acumula {int(fc.al)} alertas" + (f" (empate con {J(n for n in n_al if n != crit)}; desempata por tareas por entregar)." if len(n_al) > 1 else "."), "Indicadores: total de tareas (↑), por entregar (↑), nota promedio (↓) frente a la media de todas las materias."),
 ("p47", "P47 · Decisión a partir de los datos", f"{crit}: {int(fc.tot)} tareas (media {med.tot:.1f}), nota {fc.nota:.2f} (media {med.nota:.2f}), {int(fc.pen)} por entregar.", "Interpretación no comprobada con estos datos: más tareas no se traduce necesariamente en mejores notas; la causa puede ser otra.")])]

# 4) HTML autocontenido
def img(k):
    f = next((AQUI / "graficas").glob(f"{k}_*.png"), None)
    return f"data:image/png;base64,{base64.b64encode(f.read_bytes()).decode()}" if f else ""
nav = "".join(f'<a href="#b{n}">{n} · {s}</a>' for n, s, _ in B)
body = "".join(f'<section id="b{n}"><h2><span>Bloque {n}</span>{s}</h2>' + "".join(
    f'<article><h3>{h}</h3><img src="{img(k)}" alt="{html.escape(h)}" loading="lazy"><p class="f"><b>Hallazgo:</b> {f}</p><p class="i"><b>Interpretación:</b> {i}</p></article>'
    for k, h, f, i in qs) + "</section>" for n, s, qs in B)
kpis = [(len(t), "Tareas totales"), (int((t.estado == "Por entregar").sum()), "Por entregar"), (f"{pg:.2f}", "Nota promedio"), (cons.idxmax(), "Materia principal")]
cards = "".join(f'<div class="k"><strong>{v}</strong><span>{l}</span></div>' for v, l in kpis)
css = (AQUI / "plantilla.css").read_text(encoding="utf-8")
doc = f'''<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Academix · Reporte analítico</title><style>{css}</style></head><body>
<header><small>CESDE · Visualización de datos</small><h1>Academix: reporte analítico</h1>
<p>{len(t)} tareas y {len(c)} registros de notas · periodo {t.fecha.min():%d/%m/%Y} a {t.fecha.max():%d/%m/%Y} · corte {HOY:%d/%m/%Y}<br>Fuente: {etq_fuente} · generado {pd.Timestamp.now():%d/%m/%Y %H:%M}</p></header>
<nav>{nav}</nav><main><div class="kpis">{cards}</div>{body}</main>
<footer>Docente: Gustavo Montoya Escobar · Generado con pandas y matplotlib desde el backend de Academix</footer></body></html>'''
out = Path(a.salida); out.mkdir(exist_ok=True); (out / "index.html").write_text(doc, encoding="utf-8")
print(f"Reporte: {out/'index.html'} ({len(doc)//1024} KB) · fuente: {etq_fuente}")
if a.front:
    dest = Path(a.front) / "public" / "reportes"; dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(out / "index.html", dest / "index.html"); print(f"Publicado en el front: {dest}")