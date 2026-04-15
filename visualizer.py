import json
from pathlib import Path


def generate_html(graph_data: dict, output_path: str = "codebase_graph.html"):
    nodes_json = json.dumps(graph_data["nodes"])
    edges_json = json.dumps(graph_data["edges"])
    root = graph_data["root"]
    total_files = graph_data["total_files"]
    total_loc = graph_data["total_loc"]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>Codebase Graph</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;700;800&display=swap');

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --bg: #0a0a0f;
    --surface: #111118;
    --border: #1e1e2e;
    --accent: #7c6af7;
    --accent2: #f97316;
    --accent3: #22d3ee;
    --text: #e2e8f0;
    --muted: #64748b;
    --node-default: #7c6af7;
    --node-hub: #f97316;
    --edge: rgba(124, 106, 247, 0.25);
  }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'JetBrains Mono', monospace;
    overflow: hidden;
    height: 100vh;
    width: 100vw;
  }}

  #app {{
    display: flex;
    height: 100vh;
    width: 100vw;
    position: relative;
  }}

  /* Sidebar */
  #sidebar {{
    width: 320px;
    min-width: 320px;
    background: var(--surface);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    z-index: 10;
    overflow: hidden;
  }}

  #sidebar-header {{
    padding: 20px;
    border-bottom: 1px solid var(--border);
  }}

  #sidebar-header h1 {{
    font-family: 'Syne', sans-serif;
    font-size: 18px;
    font-weight: 800;
    color: var(--accent);
    letter-spacing: -0.5px;
  }}

  #sidebar-header p {{
    font-size: 11px;
    color: var(--muted);
    margin-top: 4px;
    word-break: break-all;
  }}

  .stats {{
    display: flex;
    gap: 12px;
    margin-top: 14px;
  }}

  .stat {{
    flex: 1;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px;
    text-align: center;
  }}

  .stat-val {{
    font-size: 20px;
    font-weight: 700;
    color: var(--accent);
  }}

  .stat-label {{
    font-size: 10px;
    color: var(--muted);
    margin-top: 2px;
  }}

  #search-box {{
    padding: 14px 20px;
    border-bottom: 1px solid var(--border);
  }}

  #search-box input {{
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    padding: 8px 12px;
    outline: none;
    transition: border-color 0.2s;
  }}

  #search-box input:focus {{
    border-color: var(--accent);
  }}

  #file-list {{
    overflow-y: auto;
    flex: 1;
  }}

  .file-item {{
    padding: 10px 20px;
    cursor: pointer;
    border-bottom: 1px solid var(--border);
    transition: background 0.15s;
  }}

  .file-item:hover {{ background: rgba(124,106,247,0.08); }}
  .file-item.active {{ background: rgba(124,106,247,0.15); border-left: 3px solid var(--accent); }}

  .file-name {{
    font-size: 12px;
    font-weight: 600;
    color: var(--text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}

  .file-meta {{
    font-size: 10px;
    color: var(--muted);
    margin-top: 3px;
  }}

  .file-loc {{
    display: inline-block;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1px 5px;
    font-size: 9px;
    color: var(--accent2);
    margin-right: 4px;
  }}

  /* Detail panel */
  #detail-panel {{
    position: absolute;
    bottom: 24px;
    right: 24px;
    width: 300px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px;
    z-index: 20;
    display: none;
    box-shadow: 0 20px 60px rgba(0,0,0,0.6);
  }}

  #detail-panel.visible {{ display: block; }}

  #detail-panel h3 {{
    font-family: 'Syne', sans-serif;
    font-size: 14px;
    font-weight: 700;
    color: var(--accent);
    margin-bottom: 10px;
    word-break: break-all;
  }}

  .detail-row {{
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    padding: 4px 0;
    border-bottom: 1px solid var(--border);
  }}

  .detail-row:last-child {{ border-bottom: none; }}
  .detail-key {{ color: var(--muted); }}
  .detail-val {{ color: var(--text); font-weight: 600; }}

  .tag-list {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 8px;
  }}

  .tag {{
    background: rgba(124,106,247,0.15);
    border: 1px solid rgba(124,106,247,0.3);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 10px;
    color: var(--accent);
  }}

  .tag.fn {{ background: rgba(34,211,238,0.1); border-color: rgba(34,211,238,0.3); color: var(--accent3); }}

  #close-detail {{
    position: absolute;
    top: 12px;
    right: 12px;
    background: none;
    border: none;
    color: var(--muted);
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
  }}

  #close-detail:hover {{ color: var(--text); }}

  /* Canvas */
  #graph-canvas {{
    flex: 1;
    position: relative;
    overflow: hidden;
  }}

  svg {{
    width: 100%;
    height: 100%;
  }}

  .node circle {{
    cursor: pointer;
    transition: r 0.2s, opacity 0.2s;
  }}

  .node text {{
    pointer-events: none;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    fill: var(--text);
    opacity: 0.85;
  }}

  .link {{
    stroke: var(--edge);
    stroke-width: 1.5;
    fill: none;
  }}

  .link.highlighted {{
    stroke: rgba(124,106,247,0.8);
    stroke-width: 2.5;
  }}

  .node.dimmed circle {{ opacity: 0.15; }}
  .node.dimmed text {{ opacity: 0.1; }}
  .link.dimmed {{ opacity: 0.05; }}

  /* Controls */
  #controls {{
    position: absolute;
    top: 20px;
    right: 20px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    z-index: 10;
  }}

  .ctrl-btn {{
    width: 36px;
    height: 36px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-size: 16px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: border-color 0.2s, background 0.2s;
  }}

  .ctrl-btn:hover {{ border-color: var(--accent); background: rgba(124,106,247,0.1); }}

  #legend {{
    position: absolute;
    bottom: 24px;
    left: 340px;
    display: flex;
    gap: 16px;
    z-index: 10;
    font-size: 11px;
    color: var(--muted);
    align-items: center;
  }}

  .legend-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 5px;
  }}
</style>
</head>
<body>
<div id="app">
  <div id="sidebar">
    <div id="sidebar-header">
      <h1>⬡ Codebase Graph</h1>
      <p>{root}</p>
      <div class="stats">
        <div class="stat">
          <div class="stat-val">{total_files}</div>
          <div class="stat-label">files</div>
        </div>
        <div class="stat">
          <div class="stat-val">{total_loc:,}</div>
          <div class="stat-label">lines</div>
        </div>
        <div class="stat" id="edge-stat">
          <div class="stat-val" id="edge-count">—</div>
          <div class="stat-label">edges</div>
        </div>
      </div>
    </div>
    <div id="search-box">
      <input type="text" id="search" placeholder="Search files..." />
    </div>
    <div id="file-list"></div>
  </div>

  <div id="graph-canvas">
    <svg id="svg"></svg>
    <div id="controls">
      <button class="ctrl-btn" id="zoom-in" title="Zoom in">+</button>
      <button class="ctrl-btn" id="zoom-out" title="Zoom out">−</button>
      <button class="ctrl-btn" id="reset-zoom" title="Reset">⊙</button>
    </div>
    <div id="legend">
      <span><span class="legend-dot" style="background:#7c6af7"></span>Module</span>
      <span><span class="legend-dot" style="background:#f97316"></span>Hub (many deps)</span>
      <span><span class="legend-dot" style="background:#22d3ee"></span>Selected</span>
      <span style="color:#555">· Scroll to zoom · Drag to pan · Click node to inspect</span>
    </div>
  </div>

  <div id="detail-panel">
    <button id="close-detail">✕</button>
    <h3 id="detail-title"></h3>
    <div id="detail-rows"></div>
    <div id="detail-tags"></div>
  </div>
</div>

<script>
const graphData = {{
  nodes: {nodes_json},
  edges: {edges_json}
}};

// ── Setup ──────────────────────────────────────────────────
const svg = d3.select("#svg");
const width = () => document.getElementById("graph-canvas").offsetWidth;
const height = () => document.getElementById("graph-canvas").offsetHeight;

const g = svg.append("g");

const zoom = d3.zoom()
  .scaleExtent([0.1, 4])
  .on("zoom", e => g.attr("transform", e.transform));

svg.call(zoom);

// ── Degree map (for hub detection) ────────────────────────
const degreeMap = {{}};
graphData.nodes.forEach(n => degreeMap[n.id] = 0);
graphData.edges.forEach(e => {{
  degreeMap[e.source] = (degreeMap[e.source] || 0) + 1;
  degreeMap[e.target] = (degreeMap[e.target] || 0) + 1;
}});
const maxDeg = Math.max(...Object.values(degreeMap), 1);

document.getElementById("edge-count").textContent = graphData.edges.length;

// ── Radius scale ───────────────────────────────────────────
const rScale = d3.scaleSqrt().domain([0, 800]).range([6, 22]).clamp(true);

// ── Force simulation ───────────────────────────────────────
const simulation = d3.forceSimulation(graphData.nodes)
  .force("link", d3.forceLink(graphData.edges).id(d => d.id).distance(120).strength(0.4))
  .force("charge", d3.forceManyBody().strength(-300))
  .force("center", d3.forceCenter(width() / 2, height() / 2))
  .force("collision", d3.forceCollide().radius(d => rScale(d.loc) + 8));

// ── Arrowhead marker ──────────────────────────────────────
svg.append("defs").append("marker")
  .attr("id", "arrow")
  .attr("viewBox", "0 -5 10 10")
  .attr("refX", 22)
  .attr("refY", 0)
  .attr("markerWidth", 6)
  .attr("markerHeight", 6)
  .attr("orient", "auto")
  .append("path")
  .attr("d", "M0,-5L10,0L0,5")
  .attr("fill", "rgba(124,106,247,0.4)");

// ── Links ─────────────────────────────────────────────────
const link = g.append("g").selectAll("line")
  .data(graphData.edges)
  .join("line")
  .attr("class", "link")
  .attr("marker-end", "url(#arrow)");

// ── Nodes ─────────────────────────────────────────────────
const node = g.append("g").selectAll(".node")
  .data(graphData.nodes)
  .join("g")
  .attr("class", "node")
  .call(d3.drag()
    .on("start", (e, d) => {{ if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }})
    .on("drag",  (e, d) => {{ d.fx = e.x; d.fy = e.y; }})
    .on("end",   (e, d) => {{ if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }})
  )
  .on("click", (e, d) => {{ e.stopPropagation(); selectNode(d); }});

node.append("circle")
  .attr("r", d => rScale(d.loc))
  .attr("fill", d => {{
    const ratio = degreeMap[d.id] / maxDeg;
    if (ratio > 0.5) return "#f97316";
    return "#7c6af7";
  }})
  .attr("fill-opacity", 0.85)
  .attr("stroke", "#0a0a0f")
  .attr("stroke-width", 2);

node.append("text")
  .attr("dy", d => rScale(d.loc) + 12)
  .attr("text-anchor", "middle")
  .text(d => d.id.split(".").pop());

svg.on("click", () => clearSelection());

// ── Tick ──────────────────────────────────────────────────
simulation.on("tick", () => {{
  link
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y);

  node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
}});

// ── Selection logic ───────────────────────────────────────
let selectedId = null;

function selectNode(d) {{
  selectedId = d.id;

  const connected = new Set([d.id]);
  graphData.edges.forEach(e => {{
    if (e.source.id === d.id || e.source === d.id) connected.add(e.target.id || e.target);
    if (e.target.id === d.id || e.target === d.id) connected.add(e.source.id || e.source);
  }});

  node.classed("dimmed", n => !connected.has(n.id));
  link.classed("dimmed", e => {{
    const s = e.source.id || e.source;
    const t = e.target.id || e.target;
    return s !== d.id && t !== d.id;
  }});
  link.classed("highlighted", e => {{
    const s = e.source.id || e.source;
    const t = e.target.id || e.target;
    return s === d.id || t === d.id;
  }});

  node.select("circle")
    .attr("stroke", n => n.id === d.id ? "#22d3ee" : "#0a0a0f")
    .attr("stroke-width", n => n.id === d.id ? 3 : 2);

  showDetail(d);

  // Highlight in sidebar
  document.querySelectorAll(".file-item").forEach(el => {{
    el.classList.toggle("active", el.dataset.id === d.id);
  }});
}}

function clearSelection() {{
  selectedId = null;
  node.classed("dimmed", false);
  link.classed("dimmed", false).classed("highlighted", false);
  node.select("circle").attr("stroke", "#0a0a0f").attr("stroke-width", 2);
  document.getElementById("detail-panel").classList.remove("visible");
  document.querySelectorAll(".file-item").forEach(el => el.classList.remove("active"));
}}

// ── Detail panel ──────────────────────────────────────────
function showDetail(d) {{
  const panel = document.getElementById("detail-panel");
  document.getElementById("detail-title").textContent = d.id;

  const connectedEdges = graphData.edges.filter(e => {{
    const s = e.source.id || e.source;
    const t = e.target.id || e.target;
    return s === d.id || t === d.id;
  }});

  const rows = [
    ["File", d.path],
    ["Lines of code", d.loc.toLocaleString()],
    ["Connections", connectedEdges.length],
    ["Classes", d.classes.length || "—"],
    ["Functions", d.functions.length || "—"],
  ];

  document.getElementById("detail-rows").innerHTML = rows.map(([k, v]) =>
    `<div class="detail-row"><span class="detail-key">${{k}}</span><span class="detail-val">${{v}}</span></div>`
  ).join("");

  let tagsHTML = '<div class="tag-list">';
  d.classes.forEach(c => tagsHTML += `<span class="tag">${{c}}</span>`);
  d.functions.slice(0, 8).forEach(f => tagsHTML += `<span class="tag fn">${{f}}()</span>`);
  tagsHTML += "</div>";
  document.getElementById("detail-tags").innerHTML = tagsHTML;

  panel.classList.add("visible");
}}

document.getElementById("close-detail").addEventListener("click", clearSelection);

// ── Sidebar file list ─────────────────────────────────────
const fileList = document.getElementById("file-list");

function renderFileList(nodes) {{
  fileList.innerHTML = nodes.map(n => `
    <div class="file-item" data-id="${{n.id}}" onclick="focusNode('${{n.id}}')">
      <div class="file-name">${{n.id.split(".").pop()}}</div>
      <div class="file-meta">
        <span class="file-loc">${{n.loc}} loc</span>
        ${{n.id}}
      </div>
    </div>
  `).join("");
}}

renderFileList(graphData.nodes);

window.focusNode = function(id) {{
  const d = graphData.nodes.find(n => n.id === id);
  if (!d) return;
  selectNode(d);

  // Pan to node
  const t = d3.zoomTransform(svg.node());
  const x = width() / 2 - t.k * d.x;
  const y = height() / 2 - t.k * d.y;
  svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity.translate(x, y).scale(t.k));
}};

// ── Search ────────────────────────────────────────────────
document.getElementById("search").addEventListener("input", e => {{
  const q = e.target.value.toLowerCase();
  const filtered = q
    ? graphData.nodes.filter(n => n.id.toLowerCase().includes(q) || n.path.toLowerCase().includes(q))
    : graphData.nodes;
  renderFileList(filtered);
}});

// ── Zoom controls ─────────────────────────────────────────
document.getElementById("zoom-in").addEventListener("click", () =>
  svg.transition().call(zoom.scaleBy, 1.4));
document.getElementById("zoom-out").addEventListener("click", () =>
  svg.transition().call(zoom.scaleBy, 0.7));
document.getElementById("reset-zoom").addEventListener("click", () =>
  svg.transition().call(zoom.transform, d3.zoomIdentity
    .translate(width() / 2, height() / 2).scale(1)
    .translate(-width() / 2, -height() / 2)));
</script>
</body>
</html>"""

    Path(output_path).write_text(html, encoding="utf-8")
    return output_path
