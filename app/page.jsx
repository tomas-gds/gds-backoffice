"use client";

import { useState } from "react";
import { ArrowRight, BookOpenText, FlaskConical, Monitor, UserRound } from "lucide-react";
import DatabaseMapper from "@/features/database-mapper/DatabaseMapper";
import PubmedScraper from "@/features/pubmed-scraper/PubmedScraper";
import AccountDialog from "@/features/shared/AccountDialog";

const ACCOUNT_KEY = "tools-workspace.account.v1";
const EMPTY_ACCOUNT = { email: "", pubmedApiKey: "" };

function WorkspaceCard({ children, onClick, disabled = false }) {
  return <button type="button" onClick={onClick} disabled={disabled} className={`group relative flex min-h-[290px] flex-col rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm ${disabled ? "" : "transition hover:-translate-y-0.5 hover:border-cyan-300 hover:shadow-md"}`}>{children}</button>;
}

export default function Home() {
  const [activeTool, setActiveTool] = useState(null);
  const [account, setAccount] = useState(() => {
    if (typeof window === "undefined") return EMPTY_ACCOUNT;
    try {
      const saved = window.localStorage.getItem(ACCOUNT_KEY);
      return saved ? { ...EMPTY_ACCOUNT, ...JSON.parse(saved) } : EMPTY_ACCOUNT;
    } catch {
      return EMPTY_ACCOUNT;
    }
  });
  const [accountOpen, setAccountOpen] = useState(false);
  function updateAccount(nextAccount) { setAccount(nextAccount); window.localStorage.setItem(ACCOUNT_KEY, JSON.stringify(nextAccount)); }
  if (activeTool === "database-mapper") return <><DatabaseMapper onBack={() => setActiveTool(null)} onAccount={() => setAccountOpen(true)} />{accountOpen && <AccountDialog account={account} onChange={updateAccount} onClose={() => setAccountOpen(false)} />}</>;
  if (activeTool === "pubmed-scraper") return <><PubmedScraper onBack={() => setActiveTool(null)} account={account} onAccount={() => setAccountOpen(true)} />{accountOpen && <AccountDialog account={account} onChange={updateAccount} onClose={() => setAccountOpen(false)} />}</>;
  return <><main className="min-h-screen bg-[#f4f7fa] text-slate-950"><header className="border-b border-slate-200 bg-[#0c2538] text-white"><div className="mx-auto flex max-w-[1450px] items-center justify-between px-5 py-5 lg:px-8"><div className="flex items-center gap-3"><div className="grid h-11 w-11 place-items-center rounded-xl bg-cyan-400 text-[#0c2538]"><Monitor size={23} strokeWidth={2.4} /></div><div><p className="font-bold">Tools Workspace</p><p className="text-xs text-slate-300">Your local applications</p></div></div><button type="button" onClick={() => setAccountOpen(true)} className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-slate-100 hover:bg-white/10"><UserRound size={17} />Account</button></div></header><div className="mx-auto max-w-[1450px] px-5 py-10 lg:px-8"><h1 className="text-3xl font-bold tracking-tight">Applications</h1><div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-3"><WorkspaceCard onClick={() => setActiveTool("database-mapper")}><div className="flex items-start justify-between gap-4"><img src="/database-mapper.svg" alt="" className="h-16 w-16 rounded-2xl" /><ArrowRight className="text-slate-300 transition group-hover:translate-x-1 group-hover:text-cyan-600" size={22} /></div><h2 className="mt-5 text-xl font-bold">Database Mapper</h2><p className="mt-2 text-sm leading-6 text-slate-500">Match records between two datasets, review confidence scores, resolve difficult records, and export the completed mapping.</p><span className="mt-auto pt-5 text-sm font-semibold text-cyan-700">Open application</span></WorkspaceCard><WorkspaceCard onClick={() => setActiveTool("pubmed-scraper")}><div className="flex items-start justify-between gap-4"><div className="grid h-16 w-16 place-items-center rounded-2xl bg-[#e6f8fb] text-[#087d98]"><BookOpenText size={31} strokeWidth={2} /></div><ArrowRight className="text-slate-300 transition group-hover:translate-x-1 group-hover:text-cyan-600" size={22} /></div><h2 className="mt-5 text-xl font-bold text-slate-800">PubMed Scraper</h2><p className="mt-2 text-sm leading-6 text-slate-500">Search PubMed and collect publication information for research and analysis.</p><span className="mt-auto pt-5 text-sm font-semibold text-cyan-700">Open application</span></WorkspaceCard><WorkspaceCard disabled><span className="absolute right-6 top-6 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500">Coming soon</span><div className="grid h-16 w-16 place-items-center rounded-2xl bg-[#edf0ff] text-[#5361b5]"><FlaskConical size={31} strokeWidth={2} /></div><h2 className="mt-5 text-xl font-bold text-slate-800">Clinical Trials Scraper</h2><p className="mt-2 text-sm leading-6 text-slate-500">Collect and organize clinical-trial records from selected sources.</p></WorkspaceCard></div></div></main>{accountOpen && <AccountDialog account={account} onChange={updateAccount} onClose={() => setAccountOpen(false)} />}</>;
}
