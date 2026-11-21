import { useState } from "react";
import { post } from "../api";

const SPEC: Record<string, string> = { standard: "~450 ms", hyde: "~1,200 ms", graph: "~850 ms" };
const NAME: Record<string, string> = { standard: "Standard Vector RAG", hyde: "Multi-Hypothesis HyDE", graph: "Graph RAG (LangGraph)" };

export default function Benchmark() {
  const [r, setR] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const run = async () => { setBusy(true); setErr(""); try { setR(await post("/benchmark", {})); } catch (e: any) { setErr(e.message); } setBusy(false); };
  const engines = ["standard", "hyde", "graph"];
  return (<>
    <div className="row"><button className="pri" disabled={busy} onClick={run}>{busy ? "Running benchmark…" : "Run benchmark on gold set"}</button>{err && <span style={{ color: "red" }}>{err}</span>}</div>
    {r && <table><thead><tr><th>Measured metric</th>{engines.map(e => <th key={e}>{NAME[e]}</th>)}</tr></thead><tbody>
      <tr><td>Retrieval Context Recall</td>{engines.map(e => <td key={e}>{r.summary[e].rcr.toFixed(2)}</td>)}</tr>
      <tr><td>Faithfulness (0–1)</td>{engines.map(e => <td key={e}>{r.summary[e].faithfulness.toFixed(2)}</td>)}</tr>
      <tr><td>Avg latency (ms)</td>{engines.map(e => <td key={e}>{Math.round(r.summary[e].latency_ms)} <small>(spec {SPEC[e]})</small></td>)}</tr>
      <tr><td>Retrieval / Graph / LLM (ms)</td>{engines.map(e => <td key={e}>{Math.round(r.summary[e].retrieval_ms)} / {Math.round(r.summary[e].graph_ms)} / {Math.round(r.summary[e].llm_ms)}</td>)}</tr>
    </tbody></table>}
    {r && <><h4>Per-question (category-level view)</h4><table><thead><tr><th>Question</th><th>Category</th><th>Engine</th><th>RCR</th><th>Faith.</th><th>ms</th></tr></thead><tbody>
      {r.rows.map((x: any, i: number) => <tr key={i}><td>{x.id}</td><td>{x.category}</td><td>{x.engine}</td><td>{x.rcr.toFixed(2)}</td><td>{x.faithfulness.toFixed(2)}</td><td>{Math.round(x.latency_ms)}</td></tr>)}</tbody></table></>}
    <h4>Spec expectations (PDF §5)</h4>
    <table><thead><tr><th>Metric</th>{engines.map(e => <th key={e}>{NAME[e]}</th>)}</tr></thead><tbody>
      <tr><td>Multi-hop relational</td><td>Poor</td><td>Moderate</td><td>Superior</td></tr>
      <tr><td>Vocabulary mismatch</td><td>Poor</td><td>Superior</td><td>High</td></tr>
      <tr><td>Hallucination risk</td><td>Moderate</td><td>Moderate</td><td>Lowest</td></tr>
      <tr><td>Best use case</td><td>Single-doc lookup (SOPs)</td><td>Vague regulatory inquiries</td><td>Complex Tax/M&A due diligence</td></tr></tbody></table>
  </>);
}
