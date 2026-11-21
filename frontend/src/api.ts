export const api = async (path: string, init?: RequestInit) => {
  const r = await fetch("/api" + path, init);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
  return r.json();
};
export const post = (p: string, body: unknown) =>
  api(p, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
