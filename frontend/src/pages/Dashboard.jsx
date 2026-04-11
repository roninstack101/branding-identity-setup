import { useState, useEffect, useCallback } from 'react';
import { runNextStep, runFullWorkflow, getProject, regenerate } from '../services/api';

import VariantGallery       from '../components/VariantGallery';
import Moodboard            from '../components/Moodboard';
import NamingCards          from '../components/NamingCards';
import CompetitorBattlefield from '../components/CompetitorBattlefield';
import ContentPreview       from '../components/ContentPreview';
import BrandStrategyView    from '../components/BrandStrategyView';
import MarketResearchView   from '../components/MarketResearchView';
import AgentCard            from '../components/AgentCard';

const STEPS = [
  { key: 'idea_discovery',        icon: '💡', label: 'Idea Analysis' },
  { key: 'market_research',       icon: '📊', label: 'Market Research' },
  { key: 'competitor_analysis',   icon: '🔍', label: 'Competitors' },
  { key: 'brand_strategy',        icon: '🎯', label: 'Brand Strategy' },
  { key: 'naming',                icon: '✏️', label: 'Naming' },
  { key: 'visual_identity_agent', icon: '🎨', label: 'Visual Identity' },
  { key: 'content_agent',         icon: '📝', label: 'Content' },
  { key: 'guidelines_agent',      icon: '📋', label: 'Guidelines' },
  { key: 'export_agent',          icon: '📦', label: 'Export' },
];

function renderAgentView(key, json, onRegenerate, projectId) {
  if (!json) return null;
  switch (key) {
    case 'market_research':       return <MarketResearchView   data={json} />;
    case 'competitor_analysis':   return <CompetitorBattlefield data={json} />;
    case 'brand_strategy':        return <BrandStrategyView    data={json} />;
    case 'naming':                return <NamingCards          data={json} />;
    case 'visual_identity_agent': return (
      <div className="space-y-10">
        <VariantGallery data={json} projectId={projectId} onRegenerate={onRegenerate} />
        <Moodboard      data={json} />
      </div>
    );
    case 'content_agent':         return <ContentPreview data={json} onRegenerate={onRegenerate} />;
    default:                      return null;
  }
}

export default function Dashboard({ project, onBack }) {
  const [agentOutputs, setAgentOutputs]     = useState({});
  const [status, setStatus]                 = useState(project.status);
  const [loading, setLoading]               = useState(false);
  const [runningAll, setRunningAll]         = useState(false);
  const [error, setError]                   = useState('');
  const [activeStep, setActiveStep]         = useState(null);
  const [sidebarOpen, setSidebarOpen]       = useState(false);

  const fetchState = useCallback(async () => {
    try {
      const res = await getProject(project.id);
      setAgentOutputs(res.data.agent_outputs || {});
      setStatus(res.data.project?.status || 'created');
    } catch (err) {
      console.error('Failed to fetch project state', err);
    }
  }, [project.id]);

  useEffect(() => { fetchState(); }, [fetchState]);

  // Auto-select the latest completed step
  useEffect(() => {
    const completed = STEPS.filter((s) => agentOutputs[s.key]);
    if (completed.length > 0 && !activeStep) {
      setActiveStep(completed[completed.length - 1].key);
    }
  }, [agentOutputs, activeStep]);

  const completedKeys = STEPS.filter((s) => agentOutputs[s.key]).map((s) => s.key);
  const progress      = Math.round((completedKeys.length / STEPS.length) * 100);
  const isComplete    = status === 'completed';

  const handleNextStep = async () => {
    setLoading(true); setError('');
    try {
      const res = await runNextStep(project.id);
      setStatus(res.data.status);
      await fetchState();
    } catch (err) { setError(err.response?.data?.detail || 'Step failed'); }
    finally { setLoading(false); }
  };

  const handleRunAll = async () => {
    setRunningAll(true); setError('');
    try {
      const res = await runFullWorkflow(project.id);
      setStatus(res.data.status);
      await fetchState();
    } catch (err) { setError(err.response?.data?.detail || 'Workflow failed'); }
    finally { setRunningAll(false); }
  };

  const handleRegenerate = async (agentName, feedback = '') => {
    try {
      setError('');
      await regenerate(project.id, agentName, feedback);
      await fetchState();
    } catch (err) { setError(err.response?.data?.detail || 'Regeneration failed'); }
  };

  const activeOutput = activeStep ? agentOutputs[activeStep] : null;
  const activeJson   = activeOutput?.output_json || null;

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Top bar ──────────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 bg-slate-950/90 backdrop-blur border-b border-white/5 px-4 md:px-6 py-3 flex items-center gap-3">
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-white/70 hover:text-white transition-all text-sm"
        >
          ← Back
        </button>

        {/* Mobile sidebar toggle */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="md:hidden flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white/70 text-sm"
        >
          ☰ Steps
        </button>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <div className="flex-1 min-w-0">
              <div className="text-xs text-white/40 hidden sm:block truncate">{project.idea}</div>
              <div className="flex items-center gap-2 mt-0.5">
                <div className="h-1.5 w-24 bg-white/10 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full transition-all duration-700"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <span className="text-xs text-white/40">{progress}%</span>
              </div>
            </div>
          </div>
        </div>

        <span className={`flex-shrink-0 px-3 py-1 rounded-full text-xs font-bold border ${
          isComplete
            ? 'bg-emerald-500/15 text-emerald-300 border-emerald-400/30'
            : status === 'running'
            ? 'bg-amber-500/15 text-amber-300 border-amber-400/30'
            : 'bg-slate-800/70 text-white/50 border-white/10'
        }`}>
          {status}
        </span>

        {!isComplete && (
          <div className="flex gap-2 flex-shrink-0">
            <button
              onClick={handleNextStep}
              disabled={loading || runningAll}
              className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-blue-600 to-cyan-500 text-white text-xs font-bold disabled:opacity-50 transition-all hover:opacity-90"
            >
              {loading ? '…' : '▶ Next'}
            </button>
            <button
              onClick={handleRunAll}
              disabled={loading || runningAll}
              className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white/70 text-xs font-bold disabled:opacity-50 transition-all hover:bg-white/10"
            >
              {runningAll ? '…' : '⚡ Run All'}
            </button>
          </div>
        )}
      </header>

      <div className="flex flex-1">
        {/* ── Sidebar ──────────────────────────────────────────────── */}
        <aside className={`
          fixed md:sticky top-[49px] z-20 h-[calc(100vh-49px)] md:h-[calc(100vh-49px)]
          w-60 bg-slate-950/95 md:bg-transparent border-r border-white/5
          flex-shrink-0 overflow-y-auto
          transition-transform duration-300
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}>
          <nav className="p-3 space-y-1">
            {STEPS.map((step) => {
              const isDone   = completedKeys.includes(step.key);
              const isActive = activeStep === step.key;
              return (
                <button
                  key={step.key}
                  onClick={() => { setActiveStep(step.key); setSidebarOpen(false); }}
                  disabled={!isDone}
                  className={`w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                    isActive
                      ? 'bg-blue-500/20 border border-blue-400/30 text-white'
                      : isDone
                      ? 'hover:bg-white/5 text-white/70 hover:text-white border border-transparent'
                      : 'text-white/25 cursor-not-allowed border border-transparent'
                  }`}
                >
                  <span className="text-base w-6 text-center flex-shrink-0">{step.icon}</span>
                  <span className="text-sm font-semibold flex-1 truncate">{step.label}</span>
                  {isDone && (
                    <span className={`w-2 h-2 rounded-full flex-shrink-0 ${isActive ? 'bg-blue-400' : 'bg-emerald-400/60'}`} />
                  )}
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Sidebar overlay for mobile */}
        {sidebarOpen && (
          <div className="fixed inset-0 z-10 bg-black/50 md:hidden" onClick={() => setSidebarOpen(false)} />
        )}

        {/* ── Main content ─────────────────────────────────────────── */}
        <main className="flex-1 min-w-0 p-4 md:p-8 overflow-x-hidden">
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start gap-3 text-sm text-red-300">
              <span>⚠️</span>{error}
            </div>
          )}

          {/* Empty state */}
          {completedKeys.length === 0 && (
            <div className="flex flex-col items-center justify-center h-96 text-center space-y-4">
              <div className="text-6xl opacity-30">🛰️</div>
              <h3 className="text-xl font-black text-white/50 uppercase">Pipeline Not Started</h3>
              <p className="text-white/30 max-w-sm text-sm">Click ▶ Next Step or ⚡ Run All in the top bar to begin generating your brand identity.</p>
            </div>
          )}

          {/* Active step view */}
          {activeStep && activeJson && (
            <div className="space-y-8 animate-fade-in">
              {/* Dedicated component or AgentCard fallback */}
              {renderAgentView(activeStep, activeJson, handleRegenerate, project.id) || (
                <AgentCard
                  agentName={activeStep}
                  output={activeOutput}
                  onRegenerate={handleRegenerate}
                  isExpanded={true}
                  onToggle={() => {}}
                />
              )}
            </div>
          )}

          {/* Export section (always visible when complete) */}
          {isComplete && agentOutputs.export_agent && (
            <div className="mt-10 relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-emerald-500 via-cyan-500 to-blue-500 rounded-3xl blur opacity-20 group-hover:opacity-35 transition duration-500" />
              <div className="relative bg-slate-950 rounded-3xl p-10 text-center space-y-6 border border-white/10">
                <div className="text-5xl">📦</div>
                <div>
                  <h2 className="text-3xl font-black text-white uppercase tracking-tight">Brand Kit Ready</h2>
                  <p className="text-white/50 max-w-lg mx-auto mt-3 text-sm leading-relaxed">
                    Your complete brand identity has been compiled. Download your brand kit below.
                  </p>
                </div>
                <div className="flex justify-center gap-4 flex-wrap">
                  {agentOutputs.export_agent?.output_json?.pdf_path && (
                    <a
                      href={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${agentOutputs.export_agent.output_json.pdf_download_url}`}
                      target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-3 px-8 py-4 rounded-2xl bg-white text-slate-900 font-black hover:scale-105 transition-all shadow-xl"
                    >
                      <span>📄</span> Download PDF
                    </a>
                  )}
                  {agentOutputs.export_agent?.output_json?.docx_path && (
                    <a
                      href={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${agentOutputs.export_agent.output_json.docx_download_url}`}
                      target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-3 px-8 py-4 rounded-2xl bg-white/5 border border-white/20 text-white font-black hover:scale-105 transition-all"
                    >
                      <span>📝</span> Download DOCX
                    </a>
                  )}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
