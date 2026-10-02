"use client";

import { KeyRound, Mail, X } from "lucide-react";

export default function AccountDialog({ account, onChange, onClose }) {
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/45 p-5" role="dialog" aria-modal="true" aria-labelledby="account-title">
      <section className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4"><div><h2 id="account-title" className="text-2xl font-bold">Account</h2><p className="mt-1 text-sm leading-6 text-slate-500">Settings shared by your local workspace applications.</p></div><button type="button" onClick={onClose} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900" aria-label="Close account settings"><X size={20} /></button></div>
        <div className="mt-6 space-y-5"><label className="block text-sm font-semibold text-slate-700"><span className="flex items-center gap-2"><Mail size={16} className="text-cyan-700" />PubMed contact email</span><input value={account.email} onChange={(event) => onChange({ ...account, email: event.target.value })} type="email" className="mt-2 w-full rounded-xl border border-slate-300 px-3 py-2.5 font-normal outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100" placeholder="name@company.com" /></label><label className="block text-sm font-semibold text-slate-700"><span className="flex items-center gap-2"><KeyRound size={16} className="text-cyan-700" />PubMed API key <span className="font-normal text-slate-500">(optional)</span></span><input value={account.pubmedApiKey} onChange={(event) => onChange({ ...account, pubmedApiKey: event.target.value })} type="password" className="mt-2 w-full rounded-xl border border-slate-300 px-3 py-2.5 font-normal outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100" placeholder="Paste your PubMed API key" /></label></div>
        <p className="mt-4 text-xs leading-5 text-slate-500">These settings are stored locally on this computer and are available to the workspace’s applications.</p><div className="mt-6 flex justify-end"><button type="button" onClick={onClose} className="rounded-xl bg-[#0c2538] px-5 py-2.5 font-semibold text-white hover:bg-[#143b57]">Done</button></div>
      </section>
    </div>
  );
}
