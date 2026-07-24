import { useRef, useState } from "react";
import { FileText, Paperclip, Send, Sparkles, X } from "lucide-react";
import { api, ChatResponse } from "../lib/api";

interface Turn {
  role: "user" | "genie";
  text: string;
  columns?: string[];
  rows?: any[][];
  error?: string | null;
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
        role: "genie", text: r.answer, columns: r.columns, rows: r.rows, error: r.error,
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
                    {t.text && <div className="bubble-text">{t.text}</div>}
                    {t.columns && t.columns.length > 0 && (
                      <div className="res-tbl-wrap">
                        <table className="res-tbl">
                          <thead><tr>{t.columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
                          <tbody>
                            {(t.rows || []).slice(0, 50).map((row, ri) => (
                              <tr key={ri}>{row.map((cell, ci) => <td key={ci}>{String(cell ?? "")}</td>)}</tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
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
