import { useEffect, useState } from "react";
import { api } from "../api";

const FIELDS: [string, string][] = [["chunk_size", "Chunk Size (tokens)"], ["chunk_overlap", "Chunk Overlap (tokens)"], ["hyde_n", "Multi-HyDE Passage Count (N)"], ["hop_k", "Graph Hop Radius (k)"], ["rrf_alpha", "Fusion RRF Constant (α)"]];

export default function Telemetry() {
  const [m, setM] = useState<any>(null);
  const load = () => api("/metrics").then(setM);
  useEffect(() => { load(); }, []);
  const set = async (k: string, v: number) => { await api("/hyperparams", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ [k]: v }) }); load(); };
  if (!m) return <p>Loading…</p>;
  const g = m.benchmark?.graph, last = m.last_run_timings?.graph;
  const fmt = (x?: number, d = 2) => x == null ? "–" : x.toFixed(d);
  return (<>
    <h3>Hyperparameters</h3>
    <div className="grid">{FIELDS.map(([k, l]) => <div className="card" key={k}><label>{l}<br /><input type="number" value={m.hyperparams[k]} onChange={e => set(k, +e.target.value)} /></label></div>)}</div>
    <p style={{ fontSize: 12 }}>Chunk size/overlap apply to documents ingested after the change.</p>
    <h3>KPIs (Graph RAG, from last benchmark)</h3>
    <div className="grid">
      <div className="card kpi">Retrieval Context Recall<b>{fmt(g?.rcr)}</b></div>
      <div className="card kpi">Faithfulness<b>{fmt(g?.faithfulness)}</b></div>
      <div className="card kpi">Entity-Relation Resolution Accuracy<b>{fmt(m.entity_resolution_accuracy)}</b></div>
      <div className="card kpi">End-to-End Latency (ms)<b>{fmt(g?.latency_ms, 0)}</b>
        <small>last chat: retrieval {fmt(last?.retrieval_ms, 0)} · graph {fmt(last?.graph_ms, 0)} · LLM {fmt(last?.llm_ms, 0)}</small></div>
    </div>
  </>);
}
