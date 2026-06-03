import { useEffect, useMemo, useState } from "react";
import axios from "axios";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const API_BASE = "http://127.0.0.1:8000";
const DRIVER_1_COLOR = "#22d3ee";
const DRIVER_2_COLOR = "#f97316";
const DELTA_COLOR = "#a3e635";

const quickQuestions = [
  "Why did VER lose pace after lap 34?",
  "Who managed tyres better in the middle stint?",
  "Was the pace loss strategy or degradation?",
];

const workspaceViews = [
  { id: "overview", label: "Overview" },
  { id: "agents", label: "Agents" },
  { id: "strategy", label: "Strategy" },
  { id: "engineer", label: "Ask Engineer" },
];

const agentAccents = {
  "Telemetry Agent": "border-cyan-300/25 bg-cyan-300/[0.055] text-cyan-100",
  "Strategy Agent": "border-orange-300/25 bg-orange-300/[0.055] text-orange-100",
  "Race Context Agent": "border-lime-300/25 bg-lime-300/[0.055] text-lime-100",
  "Comparison Agent": "border-sky-300/25 bg-sky-300/[0.055] text-sky-100",
  "LLM Explanation Agent": "border-fuchsia-300/25 bg-fuchsia-300/[0.055] text-fuchsia-100",
};

function formatValue(value, suffix = "") {
  return value === "--" || value === null || Number.isNaN(value)
    ? "--"
    : `${value}${suffix}`;
}

function StatCard({ label, value, accent = "text-slate-100", detail }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.045] p-4 shadow-[0_18px_70px_rgba(0,0,0,0.22)]">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
        {label}
      </p>
      <div className={`mt-3 text-3xl font-black ${accent}`}>{value}</div>
      {detail ? <p className="mt-2 text-sm text-slate-400">{detail}</p> : null}
    </div>
  );
}

function Panel({ title, eyebrow, children, className = "" }) {
  return (
    <section
      className={`min-w-0 rounded-lg border border-white/10 bg-[#101827]/90 p-5 shadow-[0_24px_90px_rgba(0,0,0,0.28)] ${className}`}
    >
      <div className="mb-5">
        {eyebrow ? (
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-300/80">
            {eyebrow}
          </p>
        ) : null}
        <h2 className="mt-2 text-2xl font-black text-slate-50">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function EmptyState({ label }) {
  return (
    <div className="flex h-full min-h-[220px] items-center justify-center rounded-lg border border-dashed border-white/10 bg-slate-950/30 text-sm text-slate-500">
      {label}
    </div>
  );
}

function buildStrategyData(strategy) {
  return strategy.map((item, index) => ({
    lap: Number(item.lap) || index + 1,
    Soft: item.compound === "SOFT" ? Number(item.tyreLife) || 0 : 0,
    Medium: item.compound === "MEDIUM" ? Number(item.tyreLife) || 0 : 0,
    Hard: item.compound === "HARD" ? Number(item.tyreLife) || 0 : 0,
  }));
}

function TyreStrategyChart({ driver, data }) {
  return (
    <div className="min-w-0">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h3 className="text-lg font-black text-slate-100">{driver}</h3>
        <span className="rounded-md border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs font-bold text-slate-400">
          {data.length} laps
        </span>
      </div>
      <div className="h-[260px] min-h-[220px] min-w-0">
        {data.length ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              barCategoryGap={1}
              margin={{ top: 8, right: 10, left: -10, bottom: 8 }}
            >
              <CartesianGrid stroke="#243244" strokeDasharray="4 4" />
              <XAxis dataKey="lap" stroke="#94a3b8" tickLine={false} />
              <YAxis stroke="#94a3b8" tickLine={false} width={42} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0b1220",
                  border: "1px solid rgba(255,255,255,0.12)",
                  borderRadius: "8px",
                  color: "#e2e8f0",
                }}
                labelFormatter={(label) => `Lap ${label}`}
              />
              <Bar dataKey="Soft" fill="#ef4444" radius={[3, 3, 0, 0]} />
              <Bar dataKey="Medium" fill="#facc15" radius={[3, 3, 0, 0]} />
              <Bar dataKey="Hard" fill="#e5e7eb" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <EmptyState label={`No tyre strategy data returned for ${driver}.`} />
        )}
      </div>
    </div>
  );
}

function AgentCard({ agent }) {
  const accent =
    agentAccents[agent.name] ||
    "border-white/10 bg-white/[0.04] text-slate-100";

  return (
    <article className={`rounded-lg border p-4 ${accent}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-black">{agent.name}</h3>
          <p className="mt-1 text-xs font-bold uppercase tracking-[0.18em] text-slate-400">
            {agent.status}
          </p>
        </div>
        <span className="shrink-0 rounded-md border border-white/10 bg-black/20 px-2.5 py-1 text-xs font-black text-slate-200">
          {agent.confidence}
        </span>
      </div>

      <p className="mt-4 text-sm leading-6 text-slate-200">{agent.summary}</p>

      <div className="mt-4 space-y-2">
        {(agent.evidence || []).slice(0, 4).map((item) => (
          <div
            key={item}
            className="rounded-md border border-white/10 bg-black/20 px-3 py-2 text-xs leading-5 text-slate-300"
          >
            {item}
          </div>
        ))}
      </div>
    </article>
  );
}

export default function Telemetry() {
  const [drivers, setDrivers] = useState([]);
  const [driver1, setDriver1] = useState("VER");
  const [driver2, setDriver2] = useState("NOR");
  const [laps, setLaps] = useState([]);
  const [analysis, setAnalysis] = useState([]);
  const [agents, setAgents] = useState([]);
  const [strategy1, setStrategy1] = useState([]);
  const [strategy2, setStrategy2] = useState([]);
  const [engineerAnswer, setEngineerAnswer] = useState(null);
  const [llmStatus, setLlmStatus] = useState({ provider: "fallback", model: null, error: null });
  const [questionIntent, setQuestionIntent] = useState("summary");
  const [question, setQuestion] = useState(quickQuestions[0]);
  const [activeView, setActiveView] = useState("overview");
  const [loading, setLoading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");

  const fetchDrivers = async () => {
    try {
      const response = await axios.get(`${API_BASE}/drivers`);
      setDrivers(response.data.drivers || []);
    } catch {
      setError("Backend is not reachable. Start FastAPI on port 8000.");
    }
  };

  const askRaceEngineer = async (prompt = question) => {
    try {
      setAsking(true);
      const response = await axios.get(`${API_BASE}/race-engineer`, {
        params: { question: prompt, driver1, driver2 },
      });
      setEngineerAnswer(response.data);
      setAnalysis(response.data.analysis || []);
      setAgents(response.data.agents || []);
      setLlmStatus(response.data.llm || { provider: "fallback", model: null, error: null });
      setQuestionIntent(response.data.intent || "summary");
      setError("");
    } catch {
      setError("Race engineer analysis failed. Check the backend terminal.");
    } finally {
      setAsking(false);
    }
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      setError("");

      const [telemetryResponse, analysisResponse, strategy1Response, strategy2Response] =
        await Promise.all([
          axios.get(`${API_BASE}/compare`, { params: { driver1, driver2 } }),
          axios.get(`${API_BASE}/ai-analysis`, { params: { driver1, driver2 } }),
          axios.get(`${API_BASE}/strategy`, { params: { driver: driver1 } }),
          axios.get(`${API_BASE}/strategy`, { params: { driver: driver2 } }),
        ]);

      setLaps(telemetryResponse.data.comparison || []);
      setAnalysis(analysisResponse.data.analysis || []);
      setEngineerAnswer({
        answer: analysisResponse.data.answer,
        metrics: analysisResponse.data.metrics || {},
      });
      setLlmStatus(analysisResponse.data.llm || { provider: "fallback", model: null, error: null });
      setQuestionIntent(analysisResponse.data.intent || "summary");
      setAgents(analysisResponse.data.agents || []);
      setStrategy1(strategy1Response.data.strategy || []);
      setStrategy2(strategy2Response.data.strategy || []);
    } catch {
      setError("Could not load telemetry. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial API hydration for this dashboard.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchDrivers();
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const strategy1Data = useMemo(() => buildStrategyData(strategy1), [strategy1]);
  const strategy2Data = useMemo(() => buildStrategyData(strategy2), [strategy2]);

  const stats = useMemo(() => {
    const empty = {
      fastest1: "--",
      fastest2: "--",
      avg1: "--",
      avg2: "--",
      delta: "--",
      totalLaps: 0,
      advantage: "--",
      consistency1: "--",
      consistency2: "--",
    };

    if (!laps.length) return empty;

    const driver1Laps = laps
      .map((lap) => Number(lap[driver1]))
      .filter((value) => Number.isFinite(value));
    const driver2Laps = laps
      .map((lap) => Number(lap[driver2]))
      .filter((value) => Number.isFinite(value));

    if (!driver1Laps.length || !driver2Laps.length) return empty;

    const average = (values) =>
      values.reduce((total, value) => total + value, 0) / values.length;
    const consistency = (values) => {
      const avg = average(values);
      const variance =
        values.reduce((total, value) => total + (value - avg) ** 2, 0) /
        values.length;
      return Math.max(0, 100 - Math.sqrt(variance) * 10).toFixed(1);
    };

    const avg1 = average(driver1Laps);
    const avg2 = average(driver2Laps);

    return {
      fastest1: Math.min(...driver1Laps).toFixed(2),
      fastest2: Math.min(...driver2Laps).toFixed(2),
      avg1: avg1.toFixed(2),
      avg2: avg2.toFixed(2),
      delta: Math.abs(avg1 - avg2).toFixed(2),
      totalLaps: laps.length,
      advantage: avg1 < avg2 ? driver1 : driver2,
      consistency1: consistency(driver1Laps),
      consistency2: consistency(driver2Laps),
    };
  }, [laps, driver1, driver2]);

  const driverOptions = drivers.length ? drivers : [driver1, driver2];

  return (
    <main className="min-h-screen bg-[#070b12] text-slate-100">
      <div className="border-b border-white/10 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.18),transparent_34%),linear-gradient(135deg,#08111f_0%,#0e1726_54%,#120f0d_100%)]">
        <div className="mx-auto flex max-w-7xl flex-col gap-8 px-5 py-8 lg:px-8">
          <header className="flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.32em] text-cyan-300">
                FastF1 telemetry command center
              </p>
              <h1 className="mt-4 max-w-4xl text-5xl font-black leading-[0.95] text-white md:text-7xl">
                AI Race Engineer
              </h1>
              <p className="mt-5 max-w-2xl text-base leading-7 text-slate-300">
                Ask race questions, compare lap pace, inspect tyre life, and
                turn raw Formula 1 telemetry into a race engineer briefing.
              </p>
            </div>

            <div className="grid gap-3 rounded-lg border border-white/10 bg-black/20 p-3 backdrop-blur md:grid-cols-[1fr_1fr_auto]">
              <label className="grid gap-2 text-xs font-bold uppercase tracking-[0.2em] text-slate-400">
                Driver A
                <select
                  value={driver1}
                  onChange={(event) => setDriver1(event.target.value)}
                  className="h-11 rounded-md border border-cyan-300/25 bg-slate-950 px-3 text-sm font-bold text-cyan-100 outline-none ring-cyan-300/30 transition focus:ring-4"
                >
                  {driverOptions.map((driver) => (
                    <option key={driver} value={driver}>
                      {driver}
                    </option>
                  ))}
                </select>
              </label>

              <label className="grid gap-2 text-xs font-bold uppercase tracking-[0.2em] text-slate-400">
                Driver B
                <select
                  value={driver2}
                  onChange={(event) => setDriver2(event.target.value)}
                  className="h-11 rounded-md border border-orange-300/25 bg-slate-950 px-3 text-sm font-bold text-orange-100 outline-none ring-orange-300/30 transition focus:ring-4"
                >
                  {driverOptions.map((driver) => (
                    <option key={driver} value={driver}>
                      {driver}
                    </option>
                  ))}
                </select>
              </label>

              <button
                onClick={fetchData}
                className="h-11 self-end rounded-md bg-cyan-300 px-5 text-sm font-black text-slate-950 transition hover:bg-cyan-200 disabled:cursor-wait disabled:opacity-70"
                disabled={loading}
              >
                {loading ? "Analyzing" : "Analyze"}
              </button>
            </div>
          </header>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
            <StatCard
              label={`Fastest ${driver1}`}
              value={formatValue(stats.fastest1, "s")}
              accent="text-cyan-300"
              detail={`Avg ${formatValue(stats.avg1, "s")}`}
            />
            <StatCard
              label={`Fastest ${driver2}`}
              value={formatValue(stats.fastest2, "s")}
              accent="text-orange-300"
              detail={`Avg ${formatValue(stats.avg2, "s")}`}
            />
            <StatCard
              label="Pace Delta"
              value={formatValue(stats.delta, "s")}
              accent="text-lime-300"
              detail="Average lap gap"
            />
            <StatCard
              label="Advantage"
              value={stats.advantage}
              accent="text-white"
              detail={`${stats.totalLaps} clean laps`}
            />
            <StatCard
              label={`${driver1} Stability`}
              value={formatValue(stats.consistency1, "%")}
              accent="text-cyan-100"
              detail="Lower variance is better"
            />
            <StatCard
              label={`${driver2} Stability`}
              value={formatValue(stats.consistency2, "%")}
              accent="text-orange-100"
              detail="Race run consistency"
            />
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-5 py-6 lg:px-8">
        <nav className="mb-6 flex gap-2 overflow-x-auto rounded-lg border border-white/10 bg-white/[0.035] p-1">
          {workspaceViews.map((view) => (
            <button
              key={view.id}
              type="button"
              onClick={() => setActiveView(view.id)}
              className={`h-11 shrink-0 rounded-md px-4 text-sm font-black transition ${
                activeView === view.id
                  ? "bg-cyan-300 text-slate-950"
                  : "text-slate-400 hover:bg-white/[0.05] hover:text-white"
              }`}
            >
              {view.label}
            </button>
          ))}
        </nav>

        {activeView === "overview" ? (
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1.7fr)_minmax(320px,0.8fr)]">
            <Panel
              title={`${driver1} vs ${driver2} Lap Pace`}
              eyebrow="Telemetry trace"
              className="min-h-[540px]"
            >
              <div className="h-[430px] min-h-[320px] min-w-0">
                {loading ? (
                  <EmptyState label="Loading telemetry..." />
                ) : laps.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={laps} margin={{ top: 10, right: 20, left: 0, bottom: 8 }}>
                      <CartesianGrid stroke="#243244" strokeDasharray="4 4" />
                      <XAxis dataKey="lap" stroke="#94a3b8" tickLine={false} />
                      <YAxis
                        stroke="#94a3b8"
                        tickLine={false}
                        width={48}
                        domain={["dataMin - 1", "dataMax + 1"]}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#0b1220",
                          border: "1px solid rgba(255,255,255,0.12)",
                          borderRadius: "8px",
                          color: "#e2e8f0",
                        }}
                        labelFormatter={(label) => `Lap ${label}`}
                      />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey={driver1}
                        stroke={DRIVER_1_COLOR}
                        strokeWidth={3}
                        dot={false}
                        activeDot={{ r: 5 }}
                      />
                      <Line
                        type="monotone"
                        dataKey={driver2}
                        stroke={DRIVER_2_COLOR}
                        strokeWidth={3}
                        dot={false}
                        activeDot={{ r: 5 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState label="No clean lap data returned." />
                )}
              </div>
            </Panel>

            <Panel title="Briefing" eyebrow="Current engineer summary">
              <div className="rounded-lg border border-cyan-300/20 bg-cyan-300/[0.06] p-4">
                <p className="text-sm leading-7 text-slate-200">
                  {engineerAnswer?.answer ||
                    "Run an analysis or ask a lap-specific question to generate a race engineer briefing."}
                </p>
              </div>
              <div className="mt-4 grid gap-3">
                <button
                  type="button"
                  onClick={() => setActiveView("agents")}
                  className="h-11 rounded-md border border-white/10 bg-white/[0.04] text-sm font-black text-slate-200 transition hover:border-cyan-300/35 hover:text-white"
                >
                  Review Agents
                </button>
                <button
                  type="button"
                  onClick={() => setActiveView("engineer")}
                  className="h-11 rounded-md bg-orange-300 text-sm font-black text-slate-950 transition hover:bg-orange-200"
                >
                  Ask Follow-up
                </button>
              </div>
            </Panel>

            <Panel title="Lap Delta" eyebrow={`${driver1} minus ${driver2}`} className="xl:col-span-2">
              <div className="h-[300px] min-h-[240px] min-w-0">
                {laps.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={laps} margin={{ top: 10, right: 20, left: 0, bottom: 8 }}>
                      <CartesianGrid stroke="#243244" strokeDasharray="4 4" />
                      <XAxis dataKey="lap" stroke="#94a3b8" tickLine={false} />
                      <YAxis stroke="#94a3b8" tickLine={false} width={48} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#0b1220",
                          border: "1px solid rgba(255,255,255,0.12)",
                          borderRadius: "8px",
                          color: "#e2e8f0",
                        }}
                        formatter={(value) => [`${value}s`, "Delta"]}
                        labelFormatter={(label) => `Lap ${label}`}
                      />
                      <ReferenceLine y={0} stroke="#64748b" strokeDasharray="5 5" />
                      <Line
                        type="monotone"
                        dataKey="delta"
                        stroke={DELTA_COLOR}
                        strokeWidth={3}
                        dot={false}
                        activeDot={{ r: 5 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState label="Delta appears after telemetry loads." />
                )}
              </div>
            </Panel>
          </div>
        ) : null}

        {activeView === "agents" ? (
          <Panel
            title="Specialized Agents"
            eyebrow="Telemetry, strategy, context, comparison, explanation"
          >
            {agents.length ? (
              <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
                {agents.map((agent) => (
                  <AgentCard key={agent.name} agent={agent} />
                ))}
              </div>
            ) : (
              <EmptyState label="Run an analysis to activate the specialist agents." />
            )}
          </Panel>
        ) : null}

        {activeView === "strategy" ? (
          <Panel title="Tyre Strategy Compare" eyebrow="Stint and degradation view">
            <div className="mb-4 flex flex-wrap gap-3 text-xs font-bold uppercase tracking-[0.2em] text-slate-400">
              <span className="inline-flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-sm bg-red-500" />
                Soft
              </span>
              <span className="inline-flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-sm bg-yellow-400" />
                Medium
              </span>
              <span className="inline-flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-sm bg-slate-200" />
                Hard
              </span>
            </div>
            <div className="grid min-w-0 gap-5 lg:grid-cols-2">
              <TyreStrategyChart driver={driver1} data={strategy1Data} />
              <TyreStrategyChart driver={driver2} data={strategy2Data} />
            </div>
          </Panel>
        ) : null}

        {activeView === "engineer" ? (
          <Panel title="Race Engineer" eyebrow="Ask the pit wall">
            <form
              className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_280px]"
              onSubmit={(event) => {
                event.preventDefault();
                askRaceEngineer();
              }}
            >
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                className="min-h-36 w-full resize-none rounded-lg border border-white/10 bg-slate-950/70 p-4 text-sm leading-6 text-slate-100 outline-none ring-cyan-300/20 transition placeholder:text-slate-600 focus:ring-4"
                placeholder="Ask why a driver lost pace, whether tyres fell away, or how strategy changed the race."
              />
              <div className="grid content-start gap-3">
                <button
                  type="submit"
                  disabled={asking}
                  className="h-11 rounded-md bg-orange-300 text-sm font-black text-slate-950 transition hover:bg-orange-200 disabled:cursor-wait disabled:opacity-70"
                >
                  {asking ? "Thinking" : "Ask Race Engineer"}
                </button>
                {quickQuestions.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => {
                      setQuestion(prompt);
                      askRaceEngineer(prompt);
                    }}
                    className="rounded-md border border-white/10 bg-white/[0.04] px-3 py-2 text-left text-xs font-semibold text-slate-300 transition hover:border-cyan-300/40 hover:text-white"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </form>

            {error ? (
              <div className="mt-4 rounded-lg border border-red-400/30 bg-red-500/10 p-4 text-sm text-red-100">
                {error}
              </div>
            ) : null}

            <div className="mt-5 rounded-lg border border-cyan-300/20 bg-cyan-300/[0.06] p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-xs font-bold uppercase tracking-[0.22em] text-cyan-200">
                  Briefing
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="rounded-md border border-cyan-300/20 bg-black/20 px-2.5 py-1 text-xs font-black uppercase tracking-[0.18em] text-cyan-100">
                    {questionIntent}
                  </span>
                  <span
                    className={`rounded-md border px-2.5 py-1 text-xs font-black uppercase tracking-[0.18em] ${
                      llmStatus.provider === "ollama"
                        ? "border-lime-300/30 bg-lime-300/10 text-lime-100"
                        : "border-orange-300/30 bg-orange-300/10 text-orange-100"
                    }`}
                  >
                    {llmStatus.provider === "ollama"
                      ? `Local LLM ${llmStatus.model || ""}`.trim()
                      : "Fallback"}
                  </span>
                </div>
              </div>
              <p className="mt-3 text-sm leading-7 text-slate-200">
                {engineerAnswer?.answer ||
                  "Run an analysis or ask a lap-specific question to generate a race engineer briefing."}
              </p>
            </div>

            <div className="mt-4 grid gap-3 lg:grid-cols-2">
              {analysis.map((item) => (
                <div
                  key={item}
                  className="rounded-lg border border-white/10 bg-white/[0.035] p-4 text-sm leading-6 text-slate-300"
                >
                  {item}
                </div>
              ))}
            </div>
          </Panel>
        ) : null}
      </div>
    </main>
  );
}
