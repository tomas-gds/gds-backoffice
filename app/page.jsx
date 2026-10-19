"use client";

import { useEffect, useState } from "react";
import { ArrowRight, BookOpenText, FlaskConical, Database, UserRound } from "lucide-react";
import DatabaseMapper from "@/features/database-mapper/DatabaseMapper";
import PubmedScraper from "@/features/pubmed-scraper/PubmedScraper";
import AccountDialog from "@/features/shared/AccountDialog";

const ACCOUNT_KEY = "tools-workspace.account.v1";
const EMPTY_ACCOUNT = { email: "", pubmedApiKey: "", userFolderDirectory: "", desktopPath: "" };

function WorkspaceCard({ children, onClick, disabled = false }) {
  return <button type="button" onClick={onClick} disabled={disabled} className={`group relative flex min-h-[290px] flex-col rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm ${disabled ? "" : "transition hover:-translate-y-0.5 hover:border-[#d59dca] hover:shadow-md"}`}>{children}</button>;
}

export default function Home() {
  const [activeTool, setActiveTool] = useState(null);
  const [account, setAccount] = useState(EMPTY_ACCOUNT);
  const [accountOpen, setAccountOpen] = useState(false);

  useEffect(() => {
    let savedAccount = EMPTY_ACCOUNT;
    try {
      const saved = window.localStorage.getItem(ACCOUNT_KEY);
      if (saved) savedAccount = { ...EMPTY_ACCOUNT, ...JSON.parse(saved) };
    } catch {
      // Missing or unreadable settings should open the account dialog.
    }
    setAccount(savedAccount);
    const hasEmail = typeof savedAccount.email === "string" && savedAccount.email.trim().length > 0;
    const hasApiKey = typeof savedAccount.pubmedApiKey === "string" && savedAccount.pubmedApiKey.trim().length > 0;
    const hasUserFolder = typeof savedAccount.userFolderDirectory === "string" && savedAccount.userFolderDirectory.trim().length > 0;
    const hasDesktopPath = typeof savedAccount.desktopPath === "string" && savedAccount.desktopPath.trim().length > 0;
    setAccountOpen(!hasEmail || !hasApiKey || !hasUserFolder || !hasDesktopPath);
  }, []);

  function updateAccount(nextAccount) { setAccount(nextAccount); window.localStorage.setItem(ACCOUNT_KEY, JSON.stringify(nextAccount)); }
  if (activeTool === "database-mapper") return <><DatabaseMapper onBack={() => setActiveTool(null)} account={account} onAccount={() => setAccountOpen(true)} />{accountOpen && <AccountDialog account={account} onChange={updateAccount} onClose={() => setAccountOpen(false)} />}</>;
  if (activeTool === "pubmed-scraper") return <><PubmedScraper onBack={() => setActiveTool(null)} account={account} onAccount={() => setAccountOpen(true)} />{accountOpen && <AccountDialog account={account} onChange={updateAccount} onClose={() => setAccountOpen(false)} />}</>;
  return <><main className="min-h-screen bg-[#f5f6f7] text-[#303840]"><header className="border-b border-slate-200 bg-[#951C81] text-white"><div className="mx-auto flex max-w-[1450px] items-center justify-between px-5 py-5 lg:px-8"><div className="flex items-center gap-3"><img src="/gds-icon.png" alt="GDS logo" className="h-11 w-11 object-contain" /><div><p className="font-bold">GDS Backoffice</p><p className="text-xs text-white/80">Your local applications</p></div></div><button type="button" onClick={() => setAccountOpen(true)} className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-white hover:bg-white/10"><UserRound size={17} />Account</button></div></header><div className="mx-auto max-w-[1450px] px-5 py-10 lg:px-8"><h1 className="text-3xl font-bold tracking-tight">Applications</h1><div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-3"><WorkspaceCard onClick={() => setActiveTool("database-mapper")}><div className="flex items-start justify-between gap-4"><div className="grid h-16 w-16 place-items-center rounded-2xl bg-[#f5e8f2] text-[#951C81]"><Database size={31} strokeWidth={2} /></div><ArrowRight className="text-slate-300 transition group-hover:translate-x-1 group-hover:text-[#951C81]" size={22} /></div><h2 className="mt-5 text-xl font-bold">Database Mapper</h2><p className="mt-2 text-sm leading-6 text-[#596571]">Match records between two datasets.</p><span className="mt-auto pt-5 text-sm font-semibold text-[#951C81] group-hover:text-[#7B176B]">Open application</span></WorkspaceCard><WorkspaceCard onClick={() => setActiveTool("pubmed-scraper")}><div className="flex items-start justify-between gap-4"><div className="grid h-16 w-16 place-items-center rounded-2xl bg-[#f5e8f2] text-[#951C81]"><BookOpenText size={31} strokeWidth={2} /></div><ArrowRight className="text-slate-300 transition group-hover:translate-x-1 group-hover:text-[#951C81]" size={22} /></div><h2 className="mt-5 text-xl font-bold text-[#303840]">PubMed Scraper</h2><p className="mt-2 text-sm leading-6 text-[#596571]">Collect PubMeds for HCPs, HCOs, Companies, or a list of HCPs.</p><span className="mt-auto pt-5 text-sm font-semibold text-[#951C81] group-hover:text-[#7B176B]">Open application</span></WorkspaceCard><WorkspaceCard disabled><span className="absolute right-6 top-6 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-[#596571]">Coming soon</span><div className="grid h-16 w-16 place-items-center rounded-2xl bg-[#eef0f2] text-[#596571]"><FlaskConical size={31} strokeWidth={2} /></div><h2 className="mt-5 text-xl font-bold text-[#303840]">Clinical Trials Scraper</h2><p className="mt-2 text-sm leading-6 text-[#596571]">Collect and organize clinical-trial records from selected sources.</p></WorkspaceCard></div></div></main>{accountOpen && <AccountDialog account={account} onChange={updateAccount} onClose={() => setAccountOpen(false)} />}</>;
}
