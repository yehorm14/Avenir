import type {
  BacktestSummary, CareerDetail, GameReveal, GameRound, CareerSummary, ChangesResponse, DiscoverEval, DiscoverResponse, ExplainResponse, Market,
  Inflation, MatchRequest, MatchResponse, PathPlan, PayResponse, Quiz, Radar, Trend, Replay, Source, TrustReport,
} from "./types";

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

const post = (body: unknown): RequestInit => ({ method: "POST", body: JSON.stringify(body) });

export const api = {
  quiz: () => call<Quiz>("/api/quiz"),
  match: (req: MatchRequest) => call<MatchResponse>("/api/match", post(req)),
  career: (soc: string) => call<CareerDetail>(`/api/careers/${encodeURIComponent(soc)}`),
  changes: (socs: string[]) =>
    call<ChangesResponse>(`/api/changes?${socs.map((s) => `soc=${encodeURIComponent(s)}`).join("&")}`),
  path: (soc: string, nation: string) => call<PathPlan>(`/api/path/${encodeURIComponent(soc)}?nation=${encodeURIComponent(nation)}`),
  analyse: (req: MatchRequest & { soc: string }) => call<CareerSummary>("/api/analyse", post(req)),
  explain: (req: MatchRequest & { soc: string; question: string }) => call<ExplainResponse>("/api/explain", post(req)),
  sources: () => call<Source[]>("/api/sources"),
  backtest: (excludeBridged: boolean) => call<BacktestSummary>(`/api/backtest?exclude_bridged=${excludeBridged}`),
  replay: (year: number, excludeBridged: boolean) => call<Replay>(`/api/backtest/${year}?exclude_bridged=${excludeBridged}`),
  gameRound: (year: number, seed: number) => call<GameRound>(`/api/game/round?year=${year}&seed=${seed}`),
  gameReveal: (year: number, seed: number, picks: string[]) => call<GameReveal>("/api/game/reveal", post({ year, seed, picks })),
  pay: (socs: string[], base?: number) =>
    call<PayResponse>(`/api/pay?${socs.map((s) => `soc=${encodeURIComponent(s)}`).join("&")}${base ? `&base=${base}` : ""}`),
  inflation: (amount: number, from: number, to: number) =>
    call<Inflation>(`/api/inflation?amount=${amount}&from_year=${from}&to_year=${to}`),
  radar: (fields: string[], stage: string, nation: string) =>
    call<Radar>(`/api/radar?stage=${encodeURIComponent(stage)}&nation=${encodeURIComponent(nation)}${fields.map((f) => `&fields=${encodeURIComponent(f)}`).join("")}`),
  trends: () => call<Trend[]>("/api/trends"),
  discover: (text: string) => call<DiscoverResponse>("/api/discover", post({ text })),
  discoverEval: () => call<DiscoverEval>("/api/discover/eval"),
  trust: () => call<TrustReport>("/api/trust"),
  market: (region: string) => call<Market>(`/api/market?region=${encodeURIComponent(region)}`),
};
