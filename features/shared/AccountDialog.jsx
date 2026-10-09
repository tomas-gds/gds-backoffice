"use client";

import { useState } from "react";
import { createPortal } from "react-dom";
import { Eye, EyeOff, FolderOpen, Monitor, Info, KeyRound, Mail, X } from "lucide-react";

const INSTRUCTIONS_PATH = String.raw`GDS-Backoffice - Documents\0.0 GDS Backoffice\Instructions\Account Set Up.txt`;
const INPUT_CLASS = "mt-2 w-full rounded-xl border border-slate-300 px-3 py-2.5 font-normal outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100";

function InfoTip({ id, label, children }) {
  const [position, setPosition] = useState(null);
  function show(event) {
    const bounds = event.currentTarget.getBoundingClientRect();
    setPosition({ top: Math.max(16, Math.min(bounds.bottom + 8, window.innerHeight - 160)) });
  }
  const open = position !== null;
  return (
    <span className="inline-flex font-normal" onMouseEnter={show} onMouseLeave={() => setPosition(null)} onFocus={show} onBlur={() => setPosition(null)}>
      <button type="button" aria-label={label} aria-expanded={open} aria-controls={id} aria-describedby={open ? id : undefined} onClick={show} onKeyDown={(event) => { if (event.key === "Escape") setPosition(null); }} className="rounded-full p-1 text-slate-500 hover:bg-cyan-50 hover:text-cyan-700 focus:outline-none focus:ring-2 focus:ring-cyan-500"><Info size={16} /></button>
      {open && createPortal(
        <div id={id} role="tooltip" style={{ position: "fixed", top: position.top, left: "50%", transform: "translateX(-50%)", width: "max-content", maxWidth: "calc(100vw - 32px)", zIndex: 1000 }} onMouseEnter={() => setPosition(position)} onMouseLeave={() => setPosition(null)} className="rounded-xl border border-slate-200 bg-white p-3 text-sm font-normal leading-6 text-slate-600 shadow-lg">
          <div style={{ width: 0, minWidth: "100%" }}>{children}</div>
          <div className="mt-1 overflow-x-auto whitespace-nowrap font-medium text-slate-800">{INSTRUCTIONS_PATH}.</div>
        </div>, document.body
      )}
    </span>
  );
}

export default function AccountDialog({ account, onChange, onClose }) {
  const [showApiKey, setShowApiKey] = useState(false);
  const [error, setError] = useState("");
  const hasDirectoryQuotes = [account.userFolderDirectory, account.desktopPath].some(
    (value) => typeof value === "string" && /["']/.test(value)
  );

  function finish(event) {
    event.preventDefault();
    if (hasDirectoryQuotes) return;
    if (!account.email?.trim() || !account.pubmedApiKey?.trim() || !account.userFolderDirectory?.trim() || !account.desktopPath?.trim()) {
      setError("Please enter your email, API key, User Folder directory, and Desktop directory.");
      return;
    }
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/45 p-5" role="dialog" aria-modal="true" aria-labelledby="account-title">
      <section className="max-h-[calc(100dvh-2.5rem)] w-full max-w-xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4"><div><h2 id="account-title" className="text-2xl font-bold">Account</h2><p className="mt-1 text-sm leading-6 text-slate-500">Settings shared by your local workspace applications.</p></div><button type="button" onClick={onClose} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900" aria-label="Close account settings"><X size={20} /></button></div>
        <form onSubmit={finish}>
          <div className="mt-6 space-y-5">
            <div>
              <label htmlFor="account-email" className="flex items-center gap-2 text-sm font-semibold text-slate-700"><Mail size={16} className="text-cyan-700" />Email <span className="font-normal text-slate-500">(required)</span></label>
              <input id="account-email" value={account.email ?? ""} onChange={(event) => { setError(""); onChange({ ...account, email: event.target.value }); }} type="email" required className={INPUT_CLASS} placeholder="name@company.com" />
            </div>
            <div>
              <div className="flex items-center justify-between gap-2">
                <label htmlFor="account-api-key" className="flex items-center gap-2 text-sm font-semibold text-slate-700"><KeyRound size={16} className="text-cyan-700" />PubMed API key <span className="font-normal text-slate-500">(required)</span></label>
                <InfoTip id="api-key-instructions" label="How to create a PubMed API key">For instructions on how to create an API key, please refer to the document found in</InfoTip>
              </div>
              <div className="relative">
                <input id="account-api-key" value={account.pubmedApiKey ?? ""} onChange={(event) => { setError(""); onChange({ ...account, pubmedApiKey: event.target.value }); }} type={showApiKey ? "text" : "password"} required spellCheck={false} autoCapitalize="none" className={`${INPUT_CLASS} pr-12`} placeholder="Paste your PubMed API key" />
                <button type="button" onClick={() => setShowApiKey(!showApiKey)} aria-label={showApiKey ? "Hide API key" : "Show API key"} aria-controls="account-api-key" aria-pressed={showApiKey} className="absolute bottom-1 right-1 inline-flex items-center gap-1.5 rounded-lg px-2 py-2 text-xs font-semibold text-cyan-700 hover:bg-cyan-50 focus:outline-none focus:ring-2 focus:ring-cyan-500">{showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}</button>
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between gap-2">
                <label htmlFor="account-user-folder" className="flex items-center gap-2 text-sm font-semibold text-slate-700"><FolderOpen size={16} className="text-cyan-700" />User Folder directory <span className="font-normal text-slate-500">(required)</span></label>
                <InfoTip id="user-folder-instructions" label="Where to find your User Folder directory">For instructions on where to find the directory to your User Folder in the Backoffice, please refer to the document found in</InfoTip>
              </div>
              <input id="account-user-folder" value={account.userFolderDirectory ?? ""} onChange={(event) => onChange({ ...account, userFolderDirectory: event.target.value })} type="text" required spellCheck={false} autoCapitalize="none" className={INPUT_CLASS} placeholder="Paste the directory to your User Folder" />
            </div>
            <div>
              <div className="flex items-center justify-between gap-2">
                <label htmlFor="account-desktop-path" className="flex items-center gap-2 text-sm font-semibold text-slate-700"><Monitor size={16} className="text-cyan-700" />Desktop directory <span className="font-normal text-slate-500">(required)</span></label>
                <InfoTip id="desktop-path-instructions" label="Where to find your Desktop directory">For instructions on where to find your Desktop directory, please refer to the document found in</InfoTip>
              </div>
              <input id="account-desktop-path" value={account.desktopPath ?? ""} onChange={(event) => { setError(""); onChange({ ...account, desktopPath: event.target.value }); }} type="text" required spellCheck={false} autoCapitalize="none" className={INPUT_CLASS} placeholder="Paste the directory to your Desktop folder" />
            </div>
          </div>
          {error && <p role="alert" className="mt-4 text-sm text-red-600">{error}</p>}
          <p className="mt-4 text-xs leading-5 text-slate-500">These settings are stored locally on this computer and are available to the workspace’s applications.</p>
          {hasDirectoryQuotes && <p role="alert" className="mt-4 text-sm font-medium text-red-600">Please remove all double quotation marks (&quot;) and single quotation marks (&#39;) from the User Folder directory and Desktop directory before continuing.</p>}
          <div className="mt-6 flex justify-end"><button type="submit" disabled={hasDirectoryQuotes} className="rounded-xl bg-[#0c2538] px-5 py-2.5 font-semibold text-white hover:bg-[#143b57] disabled:cursor-not-allowed disabled:opacity-50">Done</button></div>
        </form>
      </section>
    </div>
  );
}
