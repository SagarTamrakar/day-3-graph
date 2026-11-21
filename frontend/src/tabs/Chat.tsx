import { useState } from "react";
import { api, post } from "../api";
import { useApp } from "../state";

const AREAS: Record<string, string> = { tax: "Tax & Regulatory Services", grc: "Risk Advisory & Governance (GRC)", deals: "Deal Advisory & Corporate Finance" };

export default function Chat() {
  const { cfg, area, setArea } = useApp();
  const [engine, setEngine] = useState("graph");
  const [q, setQ] = useState("");
  const [msgs, setMsgs] = useState<any[]>([]);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  const upload = async (files: FileList | null) => {
    if (!files) return;
    for (const f of Array.from(files)) {
      setStatus(`Ingesting ${f.name}…`);
      const fd = new FormData(); fd.append("file", f); fd.append("area", area);
      try { const r = await api("/ingest", { method: "POST", body: fd }); setStatus(`${r.file}: ${r.chunks} chunks · graph ${r.nodes} nodes / ${r.edges} edges`); }
      catch (e: any) { setStatus("Error: " + e.message); }
    }
  };
  const send = async () => {
    if (!q.trim()) return;
    const question = q; setQ(""); setBusy(true);
    setMsgs(m => [...m, { role: "u", text: question }]);
    try { const r = await post("/chat", { question, area, engine, cfg }); setMsgs(m => [...m, { role: "a", ...r }]); }
    catch (e: any) { setMsgs(m => [...m, { role: "a", answer: "Error: " + e.message, citations: [] }]); }
    setBusy(false);
  };
  return (<>
    <div className="row">
      <select value={area} onChange={e => setArea(e.target.value)}>{Object.entries(AREAS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
      <select value={engine} onChange={e => setEngine(e.target.value)}>
        <option value="standard">Standard RAG</option><option value="hyde">HyDE RAG</option><option value="graph">Graph RAG</option></select>
    </div>
    <div className="drop" onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); upload(e.dataTransfer.files); }}>
      Drag & drop PDF / DOCX / JSON / TXT here or <input type="file" multiple onChange={e => upload(e.target.files)} />
      <div>{status}</div>
    </div>
    <div style={{ margin: "16px 0" }}>
      {msgs.map((m, i) => <div key={i} className={"msg " + m.role}>
        {m.role === "u" ? m.text : <>{m.answer}
          {m.timings && <div className="cite">engine: {m.engine} · {Math.round(m.timings.total_ms)} ms</div>}
          {m.citations?.map((c: any) => <div className="cite" key={c.label}>[{c.label}] {c.source} p.{c.page} — {c.text.slice(0, 160)}…</div>)}</>}
      </div>)}
    </div>
    <div className="row"><input type="text" value={q} placeholder="Ask a compliance question…" onChange={e => setQ(e.target.value)} onKeyDown={e => e.key === "Enter" && send()} />
      <button className="pri" disabled={busy} onClick={send}>{busy ? "Thinking…" : "Send"}</button></div>
  </>);
}
