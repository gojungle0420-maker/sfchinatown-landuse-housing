"""Render the six-tract validation as an SVG and a standalone interactive map."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
features = json.loads((ROOT / "results/tract_stock_validation.geojson").read_text())["features"]
properties = sorted((f["properties"] for f in features), key=lambda p: p["GEOID"])
paths = []
for feature in features:
    geometry = feature["geometry"]
    polygons = geometry["coordinates"]
    if geometry["type"] == "Polygon":
        polygons = [polygons]
    paths.append((feature["properties"], polygons))
vertices = [pt for _, polygons in paths for polygon in polygons for ring in polygon for pt in ring]
xs, ys = zip(*vertices)
ratio = math.cos(math.radians((max(ys) + min(ys)) / 2))
scale = min(520 / ((max(xs)-min(xs))*ratio), 460 / (max(ys)-min(ys)))

def xy(x, y):
    return 28 + (x-min(xs))*scale*ratio, 95 + (max(ys)-y)*scale

def name(p):
    code = p["GEOID"][-6:]
    return f"{int(code[:4])}.{code[4:]}"

def item(tag, x, y, content, size):
    return f'<{tag} x="{x}" y="{y}" font-size="{size}">{content}</{tag}>'

svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="860" height="610" viewBox="0 0 860 610" aria-label="Housing stock comparison across six Chinatown census tracts"><rect width="860" height="610" fill="#faf9f5"/><g font-family="Arial,sans-serif" fill="#182e35">',
       item("text",25,39,"Housing stock across six Chinatown tracts",29),
       item("text",26,70,"Difference in units · SF Planning inventory minus ACS total housing estimate",16)]
for p, polygons in paths:
    rings = []
    for polygon in polygons:
        for ring in polygon:
            coords = [xy(x, y) for x, y in ring]
            rings.append("M" + " L".join(f"{x:.2f},{y:.2f}" for x,y in coords) + " Z")
    gap = p["landuse_minus_acs_total"]
    color = "#006b75" if gap > 0 else "#a44729"
    svg.append(f'<path data-tract="{p["GEOID"]}" d="{" ".join(rings)}" fill="{color}" fill-rule="evenodd" stroke="white" stroke-width="2"><title>Tract {name(p)}: {gap:+,} units</title></path>')
    pts = [xy(*pt) for pt in polygons[0][0]]
    cross = [x*v-u*y for (x,y),(u,v) in zip(pts,pts[1:])]
    cx = sum((a[0]+b[0])*c for a,b,c in zip(pts,pts[1:],cross))/(3*sum(cross))
    cy = sum((a[1]+b[1])*c for a,b,c in zip(pts,pts[1:],cross))/(3*sum(cross))
    svg.append(f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" fill="white" font-size="14" pointer-events="none">{name(p)}</text>')
svg += [item("text",570,150,"Tract",18),item("text",700,150,"Difference",18)]
for i,p in enumerate(properties):
    y=190+44*i
    svg.extend([item("text",570,y,name(p),17),item("text",710,y,f'{p["landuse_minus_acs_total"]:+,}',17)])
svg.extend(['<rect x="570" y="473" width="16" height="16" fill="#a44729"/>',item("text",596,487,"Inventory below ACS",16),
            '<rect x="570" y="504" width="16" height="16" fill="#006b75"/>',item("text",596,518,"Inventory above ACS",16),
            item("text",26,590,"Sources: SF Planning (August 2026) · ACS 2020–2024, B25002 · TIGER/Line 2020",14),'</g></svg>'])
drawing = "".join(svg)
(ROOT / "results/tract_stock_validation.svg").write_text(drawing)
html = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chinatown housing stock comparison</title>
<style>*{box-sizing:border-box}body{max-width:980px;margin:auto;padding:22px;font:17px/1.5 system-ui;color:#182e35;background:#faf9f5}svg{width:100%;height:auto}path[data-tract],button{cursor:pointer}button{font:inherit;background:white;border:1px solid #52656a;border-radius:4px;margin:3px;padding:5px 10px}button[aria-pressed=true]{background:#183e48;color:white}path.selected{stroke:#101820;stroke-width:3}section{padding:12px 18px;background:white}dl{display:grid;grid-template-columns:auto auto;gap:4px 14px}dd{font-variant-numeric:tabular-nums;text-align:right;margin:0}</style><main>"""
html += drawing + '<p>Select a tract on the map or use a button to see its housing counts.</p><nav aria-label="Choose a tract">'
for p in properties:
    html += f'<button type="button" data-id="{p["GEOID"]}">{name(p)}</button>'
html += '</nav><section aria-live="polite"><h2></h2><dl></dl></section></main><script>const rows=' + json.dumps(properties) + """;
const fields = {full_tract_resunits:'SF Planning housing units',acs_total_units:'ACS total housing units',acs_total_moe90:'ACS total margin of error (± units, 90%)',acs_occupied_units:'ACS occupied units',acs_vacant_units:'ACS vacant units',landuse_minus_acs_total:'Inventory minus ACS total',landuse_minus_acs_occupied:'Inventory minus ACS occupied'};
function select(id){
 const row=rows.find(r=>r.GEOID===id);
 const buttons=document.querySelectorAll('button[data-id]');
 for(const b of buttons){b.setAttribute('aria-pressed',String(b.dataset.id===id));if(b.dataset.id===id)document.querySelector('h2').textContent='Tract '+b.textContent+' · GEOID '+id;}
 document.querySelectorAll('[data-tract]').forEach(p=>p.classList.toggle('selected',p.dataset.tract===id));
 const dl=document.querySelector('dl');dl.replaceChildren();
 for(const [key,label] of Object.entries(fields)){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=row[key].toLocaleString('en-US');dl.append(dt,dd);}
}
for(const b of document.querySelectorAll('button[data-id]'))b.onclick=()=>select(b.dataset.id);
for(const p of document.querySelectorAll('path[data-tract]'))p.onclick=()=>select(p.dataset.tract);
select(rows[0].GEOID);</script></html>"""
for target in ("docs/index.html", "results/tract_stock_validation.html"):
    (ROOT / target).write_text(html, encoding="utf-8")
