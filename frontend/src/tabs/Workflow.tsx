import { useMemo, useState } from "react";
import ReactFlow, { Background, Controls, Node, Edge } from "reactflow";
import "reactflow/dist/style.css";
import { post } from "../api";
import { useApp } from "../state";

const NODES = ["query_expansion", "hybrid_search", "rrf_fusion", "rerank", "synthesis"];
const LABEL: Record<string, string> = { query_expansion: "Query Expansion", hybrid_search: "Hybrid Vector/Graph Search (loops k hops)", rrf_fusion: "RRF Fusion", rerank: "Rerank", synthesis: "Synthesis" };

export default function Workflow() {
  const { cfg, setCfg, area } = useApp();
  const [q, setQ] = useState("");
  const [trace, setTrace] = useState<string[]>([]);
  const off: string[] = cfg.disabled_nodes;

  const nodes: Node[] = NODES.map((n, i) => ({ id: n, position: { x: i * 210, y: 60 + (i % 2) * 30 }, data: { label: LABEL[n] },
    style: { width: 180, background: off.includes(n) ? "#eee" : "#fff", opacity: off.includes(n) ? 0.5 : 1, border: trace.includes(n) ? "2px solid #d93954" : "1px solid #888" } }));
  const edges: Edge[] = useMemo(() => [...NODES.slice(0, -1).map((n, i) => ({ id: n, source: n, target: NODES[i + 1], animated: !off.includes(n) })),
    { id: "loop", source: "hybrid_search", target: "hybrid_search", label: "hop < k", type: "default" }], [off]);

  const run = async () => { const r = await post("/chat", { question: q, area, engine: "graph", cfg }); setTrace(r.trace || []); };
  return (<>
    <p>Click a node to toggle it on/off, then run a query to see the execution trace (red outline = executed).</p>
    <div className="card" style={{ height: 300 }}>
      <ReactFlow nodes={nodes} edges={edges} fitView onNodeClick={(_, n) => setCfg({ ...cfg, disabled_nodes: off.includes(n.id) ? off.filter(x => x !== n.id) : [...off, n.id] })}>
        <Background /><Controls /></ReactFlow></div>
    <div className="row" style={{ marginTop: 12 }}><input type="text" value={q} onChange={e => setQ(e.target.value)} placeholder="Test question" />
      <button className="pri" onClick={run}>Run Graph RAG</button></div>
    <div>Trace: {trace.join(" → ")}</div>
  </>);
}
