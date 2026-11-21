import { createContext, useContext, useState, ReactNode } from "react";
// Shared selections: KG nodes/edges and workflow nodes the user has toggled OFF (sent as retrieval config).
type Ctx = { cfg: any; setCfg: (c: any) => void; area: string; setArea: (a: string) => void };
const C = createContext<Ctx>(null as any);
export const useApp = () => useContext(C);
export function Provider({ children }: { children: ReactNode }) {
  const [cfg, setCfg] = useState({ disabled_nodes: [], kg_disabled_nodes: [], kg_disabled_edges: [] });
  const [area, setArea] = useState("tax");
  return <C.Provider value={{ cfg, setCfg, area, setArea }}>{children}</C.Provider>;
}
