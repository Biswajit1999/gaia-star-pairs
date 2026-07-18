import { Component, lazy, Suspense, useEffect, useState } from 'react';
import {
  AlertTriangle,
  ArrowDownToLine,
  Asterisk,
  BookOpen,
  Check,
  CheckCircle2,
  Database,
  ExternalLink,
  FileText,
  GitCommit,
  Orbit,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';

const GaiaHero = lazy(() => import('./GaiaHero.jsx'));

function useJson(path) {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  useEffect(() => {
    const controller = new AbortController();
    fetch(path, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
        return response.json();
      })
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => {
        if (error.name !== 'AbortError') setState({ data: null, error, loading: false });
      });
    return () => controller.abort();
  }, [path]);

  return state;
}

function formatMetric(value) {
  return typeof value === 'number' && Number.isFinite(value) ? value.toPrecision(4) : 'Not available';
}

function ChapterTitle({ number, kicker, title, copy }) {
  return (
    <div className="chapter-title">
      <div className="chapter-number">{number}</div>
      <div>
        <p>{kicker}</p>
        <h2>{title}</h2>
      </div>
      {copy && <span>{copy}</span>}
    </div>
  );
}

function MetricFeature({ metric, index }) {
  const hasInterval = metric.uncertainty_low != null && metric.uncertainty_high != null;
  return (
    <article className="metric-feature">
      <div className="metric-coordinate">M{String(index + 1).padStart(2, '0')}</div>
      <p>{metric.name.replace(/_/g, ' ')}</p>
      <strong>{formatMetric(metric.estimate)}</strong>
      <span>{metric.units}</span>
      {hasInterval && (
        <small>95% CI [{metric.uncertainty_low.toPrecision(3)}, {metric.uncertainty_high.toPrecision(3)}]</small>
      )}
      <small>n = {metric.sample_size}</small>
    </article>
  );
}

function MetricRegisterRow({ metric, index }) {
  return (
    <article className="metric-row">
      <span>{String(index + 1).padStart(2, '0')}</span>
      <p>{metric.name.replace(/_/g, ' ')}</p>
      <strong>{formatMetric(metric.estimate)}</strong>
      <small>{metric.units} · n={metric.sample_size}</small>
    </article>
  );
}

function AuditCard({ icon: Icon, title, children, className = '' }) {
  return (
    <article className={`audit-card ${className}`}>
      <div className="audit-card-heading">
        <Icon size={17} aria-hidden="true" />
        <h3>{title}</h3>
      </div>
      {children}
    </article>
  );
}

function WarningLedger({ warnings }) {
  if (warnings.loading) return <p className="ledger-loading">Reading results/warnings.json…</p>;
  if (warnings.error) {
    return <p className="ledger-error">Could not load results/warnings.json: {String(warnings.error)}</p>;
  }

  const entries = Array.isArray(warnings.data) ? warnings.data : [];
  if (entries.length === 0) {
    return (
      <div className="ledger-clear">
        <div><CheckCircle2 size={25} aria-hidden="true" /></div>
        <section>
          <p>Clear audit trail</p>
          <strong>No warnings recorded</strong>
          <span>The live results/warnings.json file contains an empty list.</span>
        </section>
        <small>0 entries</small>
      </div>
    );
  }

  return (
    <details className="warning-details">
      <summary>{entries.length} documented warning {entries.length === 1 ? 'entry' : 'entries'} · show raw ledger</summary>
      <ol>{entries.map((entry, index) => <li key={`${index}-${String(entry)}`}>{String(entry)}</li>)}</ol>
    </details>
  );
}

class HeroBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { failed: false };
  }

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (this.state.failed) return <div className="gaia-hero-fallback">Astrometry illustration unavailable.</div>;
    return this.props.children;
  }
}

export default function App() {
  const project = useJson('./project.json');
  const summary = useJson('./results/summary.json');
  const warnings = useJson('./results/warnings.json');
  const benchmarks = useJson('./results/benchmarks.json');

  if (project.loading) return <main className="loading-page">Loading astrometry ledger…</main>;
  if (project.error || !project.data) {
    return <main className="loading-page loading-failed">Could not load project.json: {String(project.error)}</main>;
  }

  const p = project.data;
  const metrics = summary.data?.metrics ?? [];
  const isDemo = summary.data?.data_kind === 'synthetic_smoke_test' || summary.data?.data_kind === 'synthetic_demo';

  return (
    <main className="sky-shell">
      <aside className="atlas-rail">
        <a className="rail-brand" href="#overview">
          <Orbit size={22} aria-hidden="true" />
          <span>Gaia pair atlas</span>
        </a>
        <nav aria-label="Report chapters">
          <a href="#findings"><span>01</span>Findings</a>
          <a href="#figures"><span>02</span>Figures</a>
          <a href="#audit"><span>03</span>Audit</a>
          <a href="#method"><span>04</span>Method</a>
          <a href="#data"><span>05</span>Data</a>
        </nav>
        <div className="rail-status">
          <Asterisk size={15} aria-hidden="true" />
          <p>{isDemo ? 'Synthetic demo' : 'Real public data'}</p>
          <span>{p.status}</span>
        </div>
        <p className="rail-credit">Astrometric consistency · Biswajit Jana</p>
      </aside>

      <div className="observatory-page">
        <header className="mission-hero" id="overview">
          <div className="hero-star-label"><Sparkles size={14} /> {p.category}</div>
          <div className="mission-copy">
            <p className="mission-index">Research atlas / 07</p>
            <h1>{p.title}</h1>
            <p className="mission-question">{p.question}</p>
            <div className="mission-tags">
              <span>{p.dataMode}</span>
              <span>Priority {p.priority}/10</span>
              <span>{summary.data ? (isDemo ? 'Demo result set' : 'Verified result set') : 'Awaiting results'}</span>
            </div>
          </div>
          <figure className="gaia-figure">
            <HeroBoundary>
              <Suspense fallback={<div className="gaia-hero-fallback">Loading survey geometry…</div>}>
                <GaiaHero />
              </Suspense>
            </HeroBoundary>
            <figcaption>Stylized illustration, not flight data</figcaption>
          </figure>
          <div className="hero-rule"><span>paired-source consistency</span><i /></div>
        </header>

        {isDemo && (
          <div className="demo-notice">
            <AlertTriangle size={18} aria-hidden="true" />
            <p>These metrics and figures are synthetic validation output, not real Gaia wide-binary measurements.</p>
          </div>
        )}

        <section className="chapter findings-chapter" id="findings">
          <ChapterTitle number="01" kicker="Measured register" title="How consistent are the pairs?" copy="The six headline quantities are read directly from results/summary.json; no values are embedded in this interface." />
          {summary.error && <p className="ledger-error">Could not load results/summary.json: {String(summary.error)}</p>}
          <div className="metric-layout">
            <div className="metric-features">
              {metrics.slice(0, 2).map((metric, index) => <MetricFeature metric={metric} index={index} key={metric.name} />)}
            </div>
            <div className="metric-register">
              {metrics.slice(2, 6).map((metric, index) => <MetricRegisterRow metric={metric} index={index + 2} key={metric.name} />)}
            </div>
          </div>
          {!summary.loading && !summary.data && !summary.error && <p className="empty-results">No results yet. Run scripts/run_analysis.py first.</p>}
        </section>

        <section className="chapter figures-chapter" id="figures">
          <ChapterTitle number="02" kicker="Evidence plates" title="Residual structure at five scales" copy="Each plate is a generated scientific SVG with a matching sidecar provenance record." />
          <div className="plate-grid">
            {p.figures.map((figure, index) => (
              <figure className={`evidence-plate plate-${index + 1}`} key={figure.id}>
                <div className="plate-label"><span>Plate {String(index + 1).padStart(2, '0')}</span><i /></div>
                <img src={`./figures/${figure.id}.svg`} alt={figure.label} loading="lazy" />
                <figcaption>{figure.label}</figcaption>
              </figure>
            ))}
          </div>
        </section>

        <section className="chapter audit-chapter" id="audit">
          <ChapterTitle number="03" kicker="Trust boundary" title="Provenance before interpretation" />
          <div className="audit-band">
            <AuditCard icon={ShieldCheck} title="Provenance boundary" className="provenance-card">
              <p className="audit-copy">{p.novelty}</p>
              <div className="validation-gate"><AlertTriangle size={17} />No result is public-ready until validation and provenance checks pass.</div>
              {summary.data?.provenance && (
                <dl className="provenance-register">
                  <div><dt><GitCommit size={14} />Git commit</dt><dd>{summary.data.provenance.git_commit}</dd></div>
                  <div><dt><FileText size={14} />Config SHA-256</dt><dd title={summary.data.provenance.config_sha256}>{summary.data.provenance.config_sha256 ?? 'n/a'}</dd></div>
                </dl>
              )}
            </AuditCard>
            <AuditCard icon={Check} title="Validation contract">
              <ol className="validation-list">
                {p.validationContract.map((item, index) => <li key={item}><span>{index + 1}</span>{item}</li>)}
              </ol>
            </AuditCard>
          </div>

          <div className="warning-ledger">
            <p className="warning-ledger-title">Pipeline warning ledger</p>
            <WarningLedger warnings={warnings} />
          </div>
        </section>

        <section className="chapter method-chapter" id="method">
          <ChapterTitle number="04" kicker="Analysis notes" title="What the scale factor can—and cannot—say" />
          <div className="method-editorial">
            <article className="method-main">
              <BookOpen size={19} aria-hidden="true" />
              <h3>Methodology</h3>
              <p>{p.methodology}</p>
            </article>
            <article className="method-notes">
              <section>
                <p>Assumptions</p>
                <ol>{p.assumptions.map((item, index) => <li key={item}><span>A{index + 1}</span>{item}</li>)}</ol>
              </section>
              <section>
                <p>Limitations</p>
                <ol>{p.limitations.map((item, index) => <li key={item}><span>L{index + 1}</span>{item}</li>)}</ol>
              </section>
            </article>
          </div>
        </section>

        <section className="chapter data-chapter" id="data">
          <ChapterTitle number="05" kicker="Reproducibility" title="Download the astrometric ledger" copy="The archive manifest records source, retrieval, checksum, selection rationale, and data terms." />
          <div className="data-layout">
            <div className="download-list">
              <a href="./manifest.csv" download><span>01</span><strong>data/manifest.csv</strong><ArrowDownToLine size={17} /></a>
              <a href="./source_catalog.csv" download><span>02</span><strong>data/source_catalog.csv</strong><ArrowDownToLine size={17} /></a>
              <a href="./results/summary.json" download><span>03</span><strong>results/summary.json</strong><ArrowDownToLine size={17} /></a>
              {benchmarks.data && <a href="./results/benchmarks.json" download><span>04</span><strong>results/benchmarks.json</strong><ArrowDownToLine size={17} /></a>}
            </div>
            <AuditCard icon={Database} title="Citation and licence" className="citation-card">
              <p>Author <strong>{p.citation.author}</strong></p>
              <p>Licence <strong>{p.citation.license}</strong></p>
              <a href={p.citation.repository}>Repository <ExternalLink size={14} /></a>
            </AuditCard>
          </div>
        </section>

        <footer className="atlas-footer"><span>Gaia wide-binary consistency audit</span><span>Research atlas · 2026</span></footer>
      </div>
    </main>
  );
}
