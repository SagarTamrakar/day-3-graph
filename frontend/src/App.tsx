import { useState } from "react";
import { Provider } from "./state";
import Chat from "./tabs/Chat";
import KGraph from "./tabs/KGraph";
import Workflow from "./tabs/Workflow";
import Telemetry from "./tabs/Telemetry";
import Benchmark from "./tabs/Benchmark";

const TABS = [["Ingestion & Chat", Chat], ["Knowledge Graph 3D", KGraph], ["LangGraph Workflow", Workflow],
  ["Hyperparameters & KPIs", Telemetry], ["Comparative Benchmark", Benchmark]] as const;

export default function App() {
  const [i, setI] = useState(0);
  const Tab = TABS[i][1];
  return (
    <Provider>
      <header><b>PwC India Advisory</b> — Standard vs HyDE vs Graph RAG</header>
      <nav>{TABS.map(([n], k) => <button key={n} className={k === i ? "on" : ""} onClick={() => setI(k)}>{k + 1}. {n}</button>)}</nav>
      <main><Tab /></main>
    </Provider>
  );
}
