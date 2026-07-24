import { useRef, useState } from "react";
import { FileText, Paperclip, Send, Sparkles, X } from "lucide-react";
import { api, ChartSpec, ChatResponse } from "../lib/api";
import { GenieChart } from "../components/charts";

interface Turn {
  role: "user" | "genie";
  text: string;
  columns?: string[];
  rows?: any[][];
  chart?: ChartSpec | null;
  error?: string | null;
}

// Minimal, safe markdown → React: paragraphs, **bold**, and "- " bullet lists.
function Markdown({ text }: { text: string }) {
  const bold = (s: string) =>
    s.split(/(\*\*[^*]+\*\*)/g).map((p, i) =>
      p.startsWith("**") && p.endsWith("**") ? <strong key={i}>{p.slice(2, -2)}</strong> : <span key={i}>{p}</span>
    );
  const blocks = text.split(/\n{2,}/);
  return (
    <>
      {blocks.map((block, bi) => {
        const lines = block.split("\n");
        const isList = lines.every((l) => /^\s*[-*]\s+/.test(l) || l.trim() === "");
        if (isList) {
          return (
            <ul className="md-list" key={bi}>
              {lines.filter((l) => l.trim()).map((l, li) => (
                <li key={li}>{bold(l.replace(/^\s*[-*]\s+/, ""))}</li>
              ))}
            </ul>
          );
        }
        return <p className="md-p" key={bi}>{lines.map((l, li) => (
          <span key={li}>{bold(l)}{li < lines.length - 1 ? <br /> : null}</span>
        ))}</p>;
      })}
    </>
  );
}

const SUGGESTIONS = [
  "What is the overall fraud rate?",
  "Which regions have the highest fraud rate?",
  "Show total fraudulent payout by policy type",
  "How many high-risk claims were filed online?",
];

export default function Assistant() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [convId, setConvId] = useState<string | null>(null);
  const [doc, setDoc] = useState<{ name: string; text: string; path: string } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function send(q: string) {
    if (!q.trim() || busy) return;
    setTurns((t) => [...t, { role: "user", text: q }]);
    setInput("");
    setBusy(true);
    try {
      const r: ChatResponse = await api.chat({
        question: q,
        conversation_id: convId,
        doc_context: doc?.text || "",
      });
      if (r.conversation_id) setConvId(r.conversation_id);
      setTurns((t) => [...t, {
        role: "genie", text: r.answer, columns: r.columns, rows: r.rows, chart: r.chart, error: r.error,
      }]);
    } catch (e) {
      setTurns((t) => [...t, { role: "genie", text: "", error: String(e) }]);
    } finally {
      setBusy(false);
    }
  }

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    try {
      const r = await api.upload(f);
      setDoc({ name: r.filename, text: r.text, path: r.volume_path });
    } catch (err) {
      alert("Upload failed: " + err);
    }
    if (fileRef.current) fileRef.current.value = "";
  }

  return (
    <div className="assistant">
      <div className="asst-main">
        <div className="asst-scroll">
          {turns.length === 0 && (
            <div className="asst-hero">
              <div className="asst-hero-ico"><Sparkles size={26} /></div>
              <h2>Fraud Chatbot</h2>
              <p>Ask questions in plain English about claims, fraud patterns, regions and payouts —
                or upload a claim document and ask questions grounded in it. Answers come back with
                detailed, plain-English explanations.</p>
              <div className="asst-sugg">
                {SUGGESTIONS.map((s) => (
                  <button key={s} className="sugg-chip" onClick={() => send(s)}>{s}</button>
                ))}
              </div>
            </div>
          )}
          {turns.map((t, i) => (
            <div key={i} className={`bubble-row ${t.role}`}>
              <div className={`bubble ${t.role}`}>
                {t.role === "genie" && <div className="bubble-tag"><Sparkles size={12} /> Fraud Chatbot</div>}
                {t.error ? (
                  <div className="bubble-err">{t.error}</div>
                ) : (
                  <>
                    {t.text && <div className="bubble-text"><Markdown text={t.text} /></div>}
                    {t.chart && (
                      <GenieChart type={t.chart.type} xKey={t.chart.x}
                        series={t.chart.series} data={t.chart.data} />
                    )}
                    {t.columns && t.columns.length > 0 && (
                      <details className="res-tbl-box" open={!t.chart}>
                        <summary>{t.chart ? "Show data table" : `${(t.rows || []).length} rows`}</summary>
                        <div className="res-tbl-wrap">
                          <table className="res-tbl">
                            <thead><tr>{t.columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
                            <tbody>
                              {(t.rows || []).slice(0, 100).map((row, ri) => (
                                <tr key={ri}>{row.map((cell, ci) => <td key={ci}>{String(cell ?? "")}</td>)}</tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </details>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}
          {busy && <div className="bubble-row genie"><div className="bubble genie"><div className="loading-dots"><i /><i /><i /></div></div></div>}
        </div>

        <div className="asst-input">
          {doc && (
            <div className="doc-chip">
              <FileText size={13} /> <span>{doc.name}</span>
              <small>→ raw/input/userdata</small>
              <button onClick={() => setDoc(null)}><X size={13} /></button>
            </div>
          )}
          <div className="input-bar">
            <input ref={fileRef} type="file" accept=".pdf,.txt,.csv,.json,.md" hidden onChange={onFile} />
            <button className="attach" title="Upload a document" onClick={() => fileRef.current?.click()}>
              <Paperclip size={17} />
            </button>
            <input
              placeholder="Ask about claims, fraud rates, regions…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send(input)}
            />
            <button className="send" disabled={busy || !input.trim()} onClick={() => send(input)}>
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
