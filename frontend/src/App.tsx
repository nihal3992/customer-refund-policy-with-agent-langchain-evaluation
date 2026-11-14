import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { api, ApiError, ChatResult, Order, Quote, Session, Ticket } from "./api";

const demoDate = new Intl.DateTimeFormat("en", {
  month: "short",
  day: "numeric",
  year: "numeric",
}).format(new Date("2026-10-22T12:00:00"));

function createConversationId() {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  return `conversation-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function Brand() {
  return (
    <Link className="brand" to="/" aria-label="Refund Lab home">
      <span className="brand-mark" aria-hidden="true">
        R
      </span>
      <span>
        <strong>Refund Lab</strong>
        <small>Policy intelligence</small>
      </span>
    </Link>
  );
}

function PublicHeader({ session }: { session: Session | null }) {
  return (
    <header className="public-header shell">
      <Brand />
      <nav aria-label="Main navigation">
        <a href="#system">How it works</a>
        <a href="#evaluation">Evaluation</a>
        <Link className="button button-small" to={session ? "/refunds" : "/login"}>
          {session ? "Open workspace" : "Try the demo"}
        </Link>
      </nav>
    </header>
  );
}

function LandingPage({ session }: { session: Session | null }) {
  return (
    <div className="marketing-page">
      <PublicHeader session={session} />
      <main>
        <section className="hero shell">
          <div className="hero-copy">
            <p className="eyebrow"><span /> Evaluation-first customer support</p>
            <h1>Refund decisions you can inspect, not just trust.</h1>
            <p className="hero-lead">
              A tool-driven assistant that combines conversational AI with a deterministic
              policy engine. Every amount is recalculated before a simulated ticket is issued.
            </p>
            <div className="hero-actions">
              <Link className="button" to={session ? "/refunds" : "/login"}>
                Explore the refund flow <span aria-hidden="true">→</span>
              </Link>
              <a className="text-link" href="#system">See the safeguards</a>
            </div>
            <div className="trust-row" aria-label="Product properties">
              <span>30-day policy</span><span>Tool traces</span><span>Synthetic data</span>
            </div>
          </div>
          <div className="hero-product" aria-label="Example refund decision">
            <div className="product-topbar">
              <span className="window-dots"><i /><i /><i /></span>
              <span>Decision preview</span>
              <span className="live-pill">Policy checked</span>
            </div>
            <div className="decision-card">
              <div className="decision-heading">
                <div><small>Eligible refund</small><strong>$45.00</strong></div>
                <div className="decision-ring">71%</div>
              </div>
              <div className="decision-line eligible">
                <span className="item-icon">BP</span>
                <span><strong>Backpack</strong><small>Purchased Oct 02</small></span>
                <span><strong>$45</strong><small>Eligible</small></span>
              </div>
              <div className="decision-line excluded">
                <span className="item-icon">WB</span>
                <span><strong>Water bottle</strong><small>Purchased Jul 25</small></span>
                <span><strong>$0</strong><small>Outside window</small></span>
              </div>
              <div className="policy-proof"><span>✓</span> Amount recomputed at action boundary</div>
            </div>
          </div>
        </section>

        <section className="proof-strip">
          <div className="shell proof-grid">
            <div><strong>7</strong><span>reference scenarios</span></div>
            <div><strong>7</strong><span>evaluation metrics</span></div>
            <div><strong>4</strong><span>inspectable tools</span></div>
            <div><strong>0</strong><span>real payments moved</span></div>
          </div>
        </section>

        <section className="system-section shell" id="system">
          <div className="section-intro">
            <p className="eyebrow"><span /> Designed for accountable automation</p>
            <h2>The model proposes. The policy decides.</h2>
            <p>Conversation and calculation have different jobs—and different trust boundaries.</p>
          </div>
          <div className="system-grid">
            <article><b>01</b><span className="feature-icon">⌕</span><h3>Retrieve</h3><p>Look up only the authenticated customer’s synthetic order history.</p></article>
            <article><b>02</b><span className="feature-icon">◇</span><h3>Evaluate</h3><p>Apply ownership, date, duplicate, and 30-day eligibility rules in Python.</p></article>
            <article><b>03</b><span className="feature-icon">✓</span><h3>Revalidate</h3><p>Recompute the requested amount before creating a simulated ticket.</p></article>
            <article><b>04</b><span className="feature-icon">↗</span><h3>Explain</h3><p>Return item-level outcomes and the tool trace behind the response.</p></article>
          </div>
        </section>

        <section className="evaluation-section" id="evaluation">
          <div className="shell evaluation-grid">
            <div>
              <p className="eyebrow light"><span /> Measured beyond the final answer</p>
              <h2>Evaluation follows the whole decision path.</h2>
              <p>DeepEval checks the trace, plan, arguments, tool order, and final response against fixed reference scenarios.</p>
            </div>
            <div className="metric-stack">
              {["Task completion", "Step efficiency", "Plan quality", "Plan adherence", "Argument correctness", "Tool correctness", "Answer correctness"].map((metric, index) => (
                <div key={metric}><span>{String(index + 1).padStart(2, "0")}</span>{metric}<i>0.8 threshold</i></div>
              ))}
            </div>
          </div>
        </section>

        <section className="cta-section shell">
          <p className="eyebrow"><span /> See the system work</p>
          <h2>Make a refund decision from start to finish.</h2>
          <p>The demo uses a synthetic customer and a fixed date, so the same request always reaches the same policy result.</p>
          <Link className="button" to={session ? "/refunds" : "/login"}>Launch interactive demo →</Link>
        </section>
      </main>
      <footer className="shell"><Brand /><p>Synthetic customers · Simulated tickets · No money moves</p><span>Policy-safe by design</span></footer>
    </div>
  );
}

function LoginPage({ session, onLogin }: { session: Session | null; onLogin: (session: Session) => void }) {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [visible, setVisible] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (session) return <Navigate to="/refunds" replace />;

  function useDemo() {
    setUsername("user126");
    setPassword("refund-demo");
    setError("");
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const authenticated = await api.login(username, password);
      onLogin(authenticated);
      navigate("/refunds");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Sign in failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <div className="login-brand"><Brand /><Link to="/">← Back to overview</Link></div>
      <section className="login-story">
        <p className="eyebrow light"><span /> Interactive product demo</p>
        <h1>Follow a refund from order history to policy decision.</h1>
        <p>Sign in as a synthetic customer to explore eligible and excluded purchases, create a simulated ticket, and inspect the assistant’s tools.</p>
        <div className="login-steps"><span><b>1</b>Review purchases</span><span><b>2</b>Check policy</span><span><b>3</b>Inspect the result</span></div>
        <small>No real customer accounts, payments, or support tickets are used.</small>
      </section>
      <section className="login-panel">
        <form className="login-card" onSubmit={submit}>
          <div><p className="eyebrow"><span /> Secure demo session</p><h2>Welcome to Refund Lab</h2><p>Use the portfolio demo account to continue.</p></div>
          <button className="demo-credential" type="button" onClick={useDemo}>
            <span><strong>Demo customer</strong><small>user126 · refund-demo</small></span><b>Use credentials</b>
          </button>
          <label>Username<input autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} placeholder="user126" required /></label>
          <label>Password<span className="password-field"><input type={visible ? "text" : "password"} autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Enter demo password" required /><button type="button" onClick={() => setVisible(!visible)}>{visible ? "Hide" : "Show"}</button></span></label>
          {error && <div className="form-error" role="alert">{error}</div>}
          <button className="button login-submit" disabled={loading}>{loading ? "Starting secure session…" : "Enter refund workspace →"}</button>
          <p className="form-note">A signed, HTTP-only cookie protects this one-hour demo session.</p>
        </form>
      </section>
    </main>
  );
}

function StatusBadge({ reason }: { reason: Order["reason"] }) {
  return <span className={`status-badge ${reason === "eligible" ? "status-good" : "status-muted"}`}>{reason === "eligible" ? "Eligible" : reason === "future purchase" ? "Future dated" : "Outside window"}</span>;
}

function RefundWorkspace({ session, onLogout }: { session: Session; onLogout: () => void }) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [quote, setQuote] = useState<Quote | null>(null);
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState<ChatResult | null>(null);
  const [chatBusy, setChatBusy] = useState(false);
  const conversationId = useMemo(createConversationId, []);

  useEffect(() => {
    api.orders().then(setOrders).catch((requestError) => setError(requestError.message));
  }, []);

  const selectedTotal = orders.filter((order) => selected.includes(order.name)).reduce((sum, order) => sum + order.price, 0);

  function toggle(name: string) {
    setSelected((current) => current.includes(name) ? current.filter((item) => item !== name) : [...current, name]);
    setQuote(null);
    setTicket(null);
    setError("");
  }

  async function checkPolicy() {
    setBusy(true); setError(""); setTicket(null);
    try { setQuote(await api.quote(selected)); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Policy check failed"); }
    finally { setBusy(false); }
  }

  async function issueTicket() {
    if (!quote) return;
    setBusy(true); setError("");
    try { setTicket(await api.ticket(selected, quote.amount)); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Ticket creation failed"); }
    finally { setBusy(false); }
  }

  async function askAssistant(event: FormEvent) {
    event.preventDefault();
    if (!message.trim()) return;
    setChatBusy(true); setChat(null);
    try { setChat(await api.chat(message, conversationId)); }
    catch (requestError) { setChat({ answer: requestError instanceof Error ? requestError.message : "Assistant unavailable", conversation: true, tools: [] }); }
    finally { setChatBusy(false); }
  }

  return (
    <div className="workspace-shell">
      <aside className="workspace-nav">
        <Brand />
        <nav><a className="active" href="#orders"><span>⌂</span>Refund workspace</a><button onClick={() => setChatOpen(true)}><span>✦</span>Policy assistant</button><a href="/#system"><span>◇</span>System design</a></nav>
        <div className="nav-safety"><span>✓</span><div><strong>Simulation mode</strong><small>No real money or tickets</small></div></div>
        <button className="user-menu" onClick={onLogout}><span>{session.username.slice(-2)}</span><div><strong>{session.username}</strong><small>Demo customer</small></div><b>↗</b></button>
      </aside>
      <main className="workspace-main">
        <header className="workspace-header"><div><p>Refund operations / <strong>New request</strong></p><h1>Review a refund</h1></div><div className="header-actions"><span>Policy date <strong>{demoDate}</strong></span><button onClick={() => setChatOpen(true)}>✦ Ask assistant</button></div></header>
        <div className="workspace-grid" id="orders">
          <section className="orders-panel">
            <div className="panel-heading"><div><span className="step-number">1</span><span><h2>Select purchases</h2><p>Choose one or more items to evaluate against the refund policy.</p></span></div><span>{selected.length} selected</span></div>
            <div className="order-list">
              {orders.map((order) => {
                const checked = selected.includes(order.name);
                return <button key={order.name} className={`order-row ${checked ? "selected" : ""}`} onClick={() => toggle(order.name)} aria-pressed={checked}><span className="check-box">{checked ? "✓" : ""}</span><span className="order-glyph">{order.name.split("_").map((part) => part[0]).join("").toUpperCase()}</span><span className="order-name"><strong>{order.name.replaceAll("_", " ")}</strong><small>Purchased {new Date(`${order.purchase_date}T12:00:00`).toLocaleDateString("en", { month: "short", day: "numeric", year: "numeric" })}</small></span><StatusBadge reason={order.reason} /><strong className="order-price">${order.price}.00</strong></button>;
              })}
            </div>
            <div className="selection-footer"><span><small>Selected purchase value</small><strong>${selectedTotal}.00</strong></span><button className="button" disabled={!selected.length || busy} onClick={checkPolicy}>{busy && !quote ? "Checking policy…" : "Check refund eligibility →"}</button></div>
          </section>

          <aside className="decision-panel">
            <div className="panel-heading compact"><div><span className="step-number">2</span><span><h2>Policy decision</h2><p>Calculated by the deterministic engine.</p></span></div></div>
            {!quote && !error && <div className="empty-decision"><span>◇</span><h3>Awaiting selection</h3><p>Select purchases and run the policy check to see an item-level decision.</p></div>}
            {error && <div className="workspace-error" role="alert"><strong>Request not completed</strong><p>{error}</p></div>}
            {quote && <div className="quote-result">
              <div className="quote-total"><small>Eligible refund</small><strong>${quote.amount}.00</strong><span>Evaluated {quote.as_of}</span></div>
              <div className="quote-lines">{quote.items.map((line) => <div key={line.name}><span className={line.amount ? "line-check good" : "line-check"}>{line.amount ? "✓" : "×"}</span><span><strong>{line.name.replaceAll("_", " ")}</strong><small>{line.reason}</small></span><b>${line.amount}.00</b></div>)}</div>
              <div className="guardrail-note"><span>⌾</span><p><strong>Action boundary protected</strong>The amount is recalculated when the ticket is created.</p></div>
              {quote.amount > 0 && !ticket && <button className="button full-button" disabled={busy} onClick={issueTicket}>{busy ? "Revalidating…" : "Create simulated ticket →"}</button>}
              {quote.amount === 0 && <div className="no-ticket">No eligible amount. A ticket will not be created.</div>}
            </div>}
            {ticket && <div className="ticket-success"><span>✓</span><p>Simulated ticket created</p><strong>{ticket.ticket_id}</strong><small>${ticket.amount}.00 approved · no money moved</small></div>}
          </aside>

          <section className="audit-panel">
            <div><span className="step-number">3</span><span><h2>Decision trace</h2><p>A concise audit trail for this request.</p></span></div>
            <ol><li className="done"><span>✓</span><p><strong>Identity scoped</strong><small>Session restricted to {session.username}</small></p></li><li className={selected.length ? "done" : ""}><span>{selected.length ? "✓" : "2"}</span><p><strong>Purchases selected</strong><small>{selected.length ? `${selected.length} item${selected.length > 1 ? "s" : ""} submitted` : "Waiting for selection"}</small></p></li><li className={quote ? "done" : ""}><span>{quote ? "✓" : "3"}</span><p><strong>Policy evaluated</strong><small>{quote ? `$${quote.amount} eligible` : "30-day rule and ownership checks"}</small></p></li><li className={ticket ? "done" : ""}><span>{ticket ? "✓" : "4"}</span><p><strong>Action revalidated</strong><small>{ticket ? ticket.ticket_id : "Required before ticket simulation"}</small></p></li></ol>
          </section>
        </div>
      </main>

      {chatOpen && <div className="drawer-backdrop" onMouseDown={() => setChatOpen(false)}><aside className="assistant-drawer" onMouseDown={(event) => event.stopPropagation()} role="dialog" aria-modal="true" aria-labelledby="assistant-title"><header><div><span>✦</span><div><h2 id="assistant-title">Policy assistant</h2><small>Authenticated as {session.username}</small></div></div><button onClick={() => setChatOpen(false)} aria-label="Close assistant">×</button></header><div className="assistant-body"><div className="assistant-intro"><span>✦</span><p>Ask about your purchases or request a refund. Model access is optional; deterministic refund controls remain available without it.</p></div>{chat && <div className="assistant-response"><small>Assistant response</small><p>{chat.answer}</p>{chat.tools.length > 0 && <details><summary>{chat.tools.length} tool call{chat.tools.length > 1 ? "s" : ""}</summary>{chat.tools.map((tool, index) => <pre key={`${tool.name}-${index}`}>{tool.name}{"\n"}{JSON.stringify(tool.arguments, null, 2)}</pre>)}</details>}</div>}</div><form onSubmit={askAssistant}><textarea value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Which of my purchases can I refund?" rows={3} /><button className="button" disabled={chatBusy || !message.trim()}>{chatBusy ? "Checking tools…" : "Send →"}</button></form></aside></div>}
    </div>
  );
}

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.session().then(setSession).catch((error) => {
      if (!(error instanceof ApiError) || error.status !== 401) console.error(error);
    }).finally(() => setLoading(false));
  }, []);

  async function logout() {
    await api.logout();
    setSession(null);
  }

  if (loading) return <div className="app-loading"><span>R</span><p>Loading Refund Lab…</p></div>;

  return <Routes>
    <Route path="/" element={<LandingPage session={session} />} />
    <Route path="/login" element={<LoginPage session={session} onLogin={setSession} />} />
    <Route path="/refunds" element={session ? <RefundWorkspace session={session} onLogout={logout} /> : <Navigate to="/login" replace />} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>;
}
