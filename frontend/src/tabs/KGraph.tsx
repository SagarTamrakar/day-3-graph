import { Component, ReactNode, useEffect, useMemo, useState } from "react";
import ForceGraph3D from "react-force-graph-3d";
import { api } from "../api";
import { useApp } from "../state";

const hasWebGL = () => {
  try { const c = document.createElement("canvas"); return !!(c.getContext("webgl2") || c.getContext("webgl")); } catch { return false; }
};

class Boundary extends Component<{ fallback: ReactNode; children: ReactNode }, { err: boolean }> {
  state = { err: false };
  static getDerivedStateFromError() { return { err: true }; }
  render() { return this.state.err ? this.props.fallback : this.props.children; }
}

// 2D orthographic projection of the same spherical layout (used when WebGL is unavailable).
function Sphere2D({ gd, cfg, toggle }: any) {
  const [rot, setRot] = useState(0);
  const W = 900, H = 540, s = 2.0;
  const pos = useMemo(() => {
    const m: Record<string, [number, number, number]> = {};
    const c = Math.cos(rot), sn = Math.sin(rot);
    gd.nodes.forEach((n: any) => { m[n.id] = [W / 2 + (n.fx * c + n.fz * sn) * s, H / 2 + n.fy * s, -n.fx * sn + n.fz * c]; });
    return m;
  }, [gd, rot]);
  return (<div>
    <div className="row">WebGL unavailable — showing 2D projection of the sphere. Rotate: <input type="range" min={0} max={6.28} step={0.05} value={rot} onChange={e => setRot(+e.target.value)} /></div>
    <svg width={W} height={H} style={{ background: "#fff", border: "1px solid #e3e6ea" }}>
      {gd.links.map((l: any, i: number) => {
        const a = pos[l.source.id ?? l.source], b = pos[l.target.id ?? l.target]; if (!a || !b) return null;
        return <line key={i} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} strokeWidth={3} style={{ cursor: "pointer" }} onClick={() => toggle("kg_disabled_edges", l.id)}
          stroke={cfg.kg_disabled_edges.includes(l.id) ? "#ccc" : "#3b6fd4"}><title>{l.relation}</title></line>;
      })}
      {[...gd.nodes].sort((p: any, q: any) => pos[p.id][2] - pos[q.id][2]).map((n: any) => (
        <g key={n.id} style={{ cursor: "pointer" }} onClick={() => toggle("kg_disabled_nodes", n.id)}>
          <circle cx={pos[n.id][0]} cy={pos[n.id][1]} r={7} fill={cfg.kg_disabled_nodes.includes(n.id) ? "#999" : "#d93954"} />
          <text x={pos[n.id][0] + 9} y={pos[n.id][1] + 4} fontSize={11}>{n.id}</text>
        </g>))}
    </svg></div>);
}

export default function KGraph() {
  const { cfg, setCfg } = useApp();
  const [data, setData] = useState<any>({ nodes: [], links: [] });
  const [err, setErr] = useState("");
  const gl = useMemo(hasWebGL, []);
  useEffect(() => { api("/graph").then(setData).catch(e => setErr(e.message)); }, []);

  const gd = useMemo(() => {
    const n = data.nodes.length, R = 120;
    return { links: data.links.map((l: any) => ({ ...l })), nodes: data.nodes.map((d: any, i: number) => {
      const y = n > 1 ? 1 - (i / (n - 1)) * 2 : 0, r = Math.sqrt(1 - y * y), th = i * 2.399963;
      return { ...d, fx: R * r * Math.cos(th), fy: R * y, fz: R * r * Math.sin(th) };
    }) };
  }, [data]);

  const toggle = (key: "kg_disabled_nodes" | "kg_disabled_edges", id: string) => {
    const cur: string[] = cfg[key];
    setCfg({ ...cfg, [key]: cur.includes(id) ? cur.filter(x => x !== id) : [...cur, id] });
  };
  const flat = <Sphere2D gd={gd} cfg={cfg} toggle={toggle} />;
  return (<>
    <div className="row">Click a node or edge to exclude/include it from retrieval. Disabled: {cfg.kg_disabled_nodes.length} nodes, {cfg.kg_disabled_edges.length} edges.
      <button onClick={() => setCfg({ ...cfg, kg_disabled_nodes: [], kg_disabled_edges: [] })}>Reset</button></div>
    {err && <p style={{ color: "red" }}>Error loading graph: {err}</p>}
    {gd.nodes.length === 0 ? <p>No graph yet — ingest a document in Tab 1 (e.g. files from data/samples), then reopen this tab.</p> :
      gl ? <Boundary fallback={flat}><div className="card" style={{ padding: 0 }}>
        <ForceGraph3D width={1000} height={560} graphData={gd as any} nodeLabel="id" linkLabel="relation"
          nodeColor={(n: any) => cfg.kg_disabled_nodes.includes(n.id) ? "#999" : "#d93954"}
          linkColor={(l: any) => cfg.kg_disabled_edges.includes(l.id) ? "#ccc" : "#3b6fd4"}
          linkWidth={1.5} linkDirectionalArrowLength={4}
          onNodeClick={(n: any) => toggle("kg_disabled_nodes", n.id)} onLinkClick={(l: any) => toggle("kg_disabled_edges", l.id)} />
      </div></Boundary> : flat}
  </>);
}
