import { useEffect, useState } from "react";
import { Bell, Database, ExternalLink, LayoutGrid, MessageSquare, Search } from "lucide-react";
import { api, Meta } from "./lib/api";
import Dashboard from "./pages/Dashboard";
import Assistant from "./pages/Assistant";

type View = "dashboard" | "assistant";

const RAIL: { key: View; label: string; icon: typeof LayoutGrid }[] = [
  { key: "dashboard", label: "Overview", icon: LayoutGrid },
  { key: "assistant", label: "Fraud Chatbot", icon: MessageSquare },
];

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [meta, setMeta] = useState<Meta | null>(null);

  useEffect(() => {
    api.meta().then(setMeta).catch(() => {});
  }, []);

  async function openUC() {
    const { url } = await api.ucLink("gold_fraud_claims");
    window.open(url, "_blank");
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="pimco">ALLIANZ</span>
          <span className="brand-div" />
          <span className="app-name">Fraud Analytics Workspace</span>
        </div>
        <div className="searchbar">
          <Search size={15} />
          <input placeholder="Search claims, policies, regions or keywords" />
        </div>
        <div className="top-right">
          <button className="uc-btn" onClick={openUC} title="Open this app's governed data in Unity Catalog">
            <Database size={15} /> Unity Catalog <ExternalLink size={12} />
          </button>
          <button className="icon-btn"><Bell size={16} /></button>
          <div className="user">
            <div className="avatar">FA</div>
            <div className="user-meta">
              <b>Fraud Analyst</b>
              <span>Claims Intelligence</span>
            </div>
          </div>
        </div>
      </header>

      <div className="body">
        <nav className="rail">
          <div className="rail-label">Fraud</div>
          {RAIL.map((r) => (
            <button
              key={r.key}
              className={`rail-item ${view === r.key ? "active" : ""}`}
              onClick={() => setView(r.key)}
            >
              <r.icon size={19} />
              <span>{r.label}</span>
            </button>
          ))}
          <div className="rail-foot">
            <div className="rail-catalog">
              <Database size={13} />
              {meta ? meta.catalog : "Unity Catalog"}
            </div>
          </div>
        </nav>

        <main className="canvas">
          {view === "dashboard" && <Dashboard />}
          {view === "assistant" && <Assistant />}
        </main>
      </div>
    </div>
  );
}
