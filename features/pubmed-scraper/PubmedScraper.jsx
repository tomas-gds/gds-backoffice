"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowLeft, BookOpenText, ChevronDown, Download, FileSpreadsheet,
  Info, LoaderCircle, Search, UserRound, X,
} from "lucide-react";
import { invoke } from "@tauri-apps/api/core";

const API = "http://127.0.0.1:8000";
const workflows = {
  author: { name: "HCPs", description: "Find the most relevant authors for a certain (rare) disease in a specific country." },
  hco: { name: "HCOs", description: "Find the most relevant HCOs for a certain (rare) disease in a specific country." },
  company: { name: "Company", description: "Search a company and choose HCP or HCO results." },
  hcp_file: { name: "Load HCP file", description: "Use names from your own CSV or Excel file to build the PubMed author search." },
};

function safeFilename(value) {
  return value.trim().replace(/[^a-z0-9]+/gi, "_").replace(/^_+|_+$/g, "") || "search";
}

function browserDownload(bytes, filename) {
  const url = URL.createObjectURL(new Blob([bytes], { type: filename.endsWith(".csv") ? "text/csv;charset=utf-8" : "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function SaveScrapeDialog({ fileName, setFileName, chooseLocation, setChooseLocation, saving, exportFormat, setExportFormat, error, onClose, onSave }) {
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/45 p-4" role="dialog" aria-modal="true" aria-labelledby="save-scrape-title">
      <section className="w-full max-w-4xl rounded-2xl bg-white p-7 shadow-2xl">
        <div className="flex items-start justify-between gap-4"><div><h2 id="save-scrape-title" className="text-2xl font-bold">Export PubMed File</h2><p className="mt-1 text-slate-500">Choose an export format and file name. The export will be saved to your desktop folder.</p></div><button type="button" onClick={onClose} disabled={saving} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 disabled:opacity-50" aria-label="Close"><X size={21} /></button></div>
        <fieldset className="mt-5"><legend className="text-sm font-semibold text-slate-700">Export format</legend><div className="mt-2 grid gap-3 sm:grid-cols-2">{[["xlsx", "Excel workbook (.xlsx)"], ["csv", "CSV file (.csv)"]].map(([value, label]) => <label key={value} className={`cursor-pointer rounded-lg border p-3 ${exportFormat === value ? "border-cyan-600 bg-cyan-50 ring-1 ring-cyan-600" : "border-slate-200 bg-white"}`}><input type="radio" name="pubmed-export-format" value={value} checked={exportFormat === value} onChange={() => setExportFormat(value)} disabled={saving} className="sr-only" /><span className="block text-sm font-semibold text-slate-800">{label}</span></label>)}</div>{exportFormat === "csv" && <p className="mt-2 text-xs text-slate-500">CSV includes PubMed Data only. Choose Excel to keep all tabs.</p>}</fieldset>
        <label className="mt-6 block text-sm font-semibold text-slate-700">File name<input value={fileName} onChange={(event) => setFileName(event.target.value)} disabled={saving} className="mt-2 w-full rounded-xl border border-slate-300 px-3 py-2.5 font-normal outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100" /></label>
        <label className="mt-4 flex items-center gap-2 text-sm font-medium text-slate-700"><input type="checkbox" checked={chooseLocation} onChange={(event) => setChooseLocation(event.target.checked)} disabled={saving} className="h-4 w-4 accent-cyan-600" />Choose a different save location</label>
        {error && <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
        <div className="mt-7 flex justify-end gap-3"><button type="button" onClick={onClose} disabled={saving} className="rounded-xl border border-slate-300 px-5 py-2.5 font-semibold hover:bg-slate-50 disabled:opacity-50">Cancel</button><button type="button" onClick={onSave} disabled={saving} className="inline-flex items-center gap-2 rounded-xl bg-[#0c2538] px-5 py-2.5 font-semibold text-white hover:bg-[#143b57] disabled:opacity-60">{saving ? <><LoaderCircle size={18} className="animate-spin" />Saving…</> : <><Download size={18} />Save export</>}</button></div>
      </section>
    </div>
  );
}

function ReviewNamesDialog({ pairs, index, setIndex, decisions, setDecisions, preparing, onContinue, onSkip }) {
  const pair = pairs[index];
  const decision = decisions[pair.id];
  const reviewed = Object.keys(decisions).length;
  const choose = (action, canonicalName = "") => setDecisions({ ...decisions, [pair.id]: { action, canonical_name: canonicalName } });
  const evidence = (name, details) => {
    const selected = decision?.action === "merge" && decision.canonical_name === name;
    return <div className={`overflow-hidden rounded-xl border bg-slate-50 ${selected ? "border-cyan-500 ring-1 ring-cyan-500" : "border-slate-200"}`}>
      <div className="flex items-start justify-between gap-3 p-4"><div><button type="button" onClick={() => choose("merge", name)} className="text-left text-xl font-bold text-slate-950 underline decoration-cyan-400 decoration-2 underline-offset-4 hover:text-cyan-800">{name}</button><p className="mt-2 text-sm text-slate-500">{details.publications} publication{details.publications === 1 ? "" : "s"} found</p></div>{selected && <span className="rounded-full bg-cyan-100 px-2.5 py-1 text-xs font-semibold text-cyan-800">Selected</span>}</div>
      <div className="border-t border-slate-200 bg-white"><div className="grid grid-cols-[auto_1fr] gap-x-4 border-b border-slate-100 bg-slate-100 px-4 py-2 text-xs font-bold uppercase tracking-wide text-slate-500"><span>#</span><span>Associated affiliation</span></div><div className="max-h-48 overflow-y-auto">{details.affiliations.length ? details.affiliations.map((item, affiliationIndex) => <div key={`${item}-${affiliationIndex}`} className="grid grid-cols-[auto_1fr] gap-x-4 border-b border-slate-100 px-4 py-3 text-sm text-slate-600 last:border-0"><span className="font-medium text-slate-400">{affiliationIndex + 1}</span><span>{item}</span></div>) : <div className="px-4 py-4 text-sm text-slate-500">No affiliation evidence found.</div>}</div></div>
    </div>;
  };
  return <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/45 p-5" role="dialog" aria-modal="true" aria-labelledby="review-name-title"><section className="mx-auto my-6 w-full max-w-5xl rounded-2xl bg-white p-7 shadow-2xl"><div className="flex items-start justify-between gap-4"><div><p className="text-sm font-semibold text-cyan-800">Review potential name mappings</p><h2 id="review-name-title" className="mt-1 text-2xl font-bold">Potential match {index + 1} of {pairs.length}</h2><p className="mt-1 text-sm text-slate-500">Click the preferred name to use it throughout the PubMed Data output, or keep the two people separate.</p></div><button type="button" onClick={onSkip} disabled={preparing} className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold hover:bg-slate-50 disabled:opacity-50">Skip review</button></div><div className="mt-6 grid gap-4 md:grid-cols-2">{evidence(pair.name_a, pair.evidence_a)}{evidence(pair.name_b, pair.evidence_b)}</div><div className="mt-5 flex justify-center"><button type="button" onClick={() => choose("separate")} className={`rounded-xl border px-5 py-3 text-left ${decision?.action === "separate" ? "border-slate-500 bg-slate-100 ring-1 ring-slate-400" : "border-slate-300 hover:border-slate-500"}`}><span className="font-semibold">Keep separate</span><span className="ml-2 text-sm text-slate-500">Do not change either name.</span></button></div><div className="mt-7 flex items-center justify-between gap-3 border-t border-slate-200 pt-5"><p className="text-sm text-slate-500">{reviewed} of {pairs.length} reviewed</p><div className="flex gap-3"><button type="button" onClick={() => setIndex(Math.max(0, index - 1))} disabled={index === 0 || preparing} className="rounded-xl border border-slate-300 px-4 py-2.5 font-semibold disabled:opacity-40">Previous</button>{index < pairs.length - 1 ? <button type="button" onClick={() => setIndex(index + 1)} disabled={!decision || preparing} className="rounded-xl bg-[#0c2538] px-5 py-2.5 font-semibold text-white disabled:opacity-40">Next match</button> : <button type="button" onClick={onContinue} disabled={reviewed !== pairs.length || preparing} className="inline-flex items-center gap-2 rounded-xl bg-[#087d98] px-5 py-2.5 font-semibold text-white disabled:opacity-40">{preparing && <LoaderCircle size={17} className="animate-spin" />}Prepare download</button>}</div></div></section></div>;
}

export default function PubmedScraper({ onBack, account, onAccount }) {
  const [mode, setMode] = useState("author");
  const [search, setSearch] = useState("");
  const [companyTarget, setCompanyTarget] = useState("author");
  const [country, setCountry] = useState("");
  const [years, setYears] = useState(5);
  const [rareDisease, setRareDisease] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [file, setFile] = useState(null);
  const [fileInfo, setFileInfo] = useState(null);
  const [sheet, setSheet] = useState("");
  const [nameColumn, setNameColumn] = useState("");
  const [fullNetwork, setFullNetwork] = useState(false);
  const [loadingFile, setLoadingFile] = useState(false);
  const [running, setRunning] = useState(false);
  const [leaveOpen, setLeaveOpen] = useState(false);
  const [stopping, setStopping] = useState(false);
  const activeRun = useRef(null);

  useEffect(() => () => {
    const active = activeRun.current;
    if (active) {
      active.controller.abort();
      fetch(`${API}/pubmed/cancel/${active.id}`, { method: "POST", keepalive: true }).catch(() => {});
      activeRun.current = null;
    }
  }, []);

  function handleBack() {
    if (activeRun.current) setLeaveOpen(true);
    else onBack();
  }

  async function stopAndLeave() {
    setStopping(true); setError("");
    const active = activeRun.current;
    try {
      if (active) {
        const response = await fetch(`${API}/pubmed/cancel/${active.id}`, { method: "POST" });
        if (!response.ok) throw new Error("Could not stop the PubMed search. Please try again.");
        active.controller.abort();
        if (activeRun.current === active) activeRun.current = null;
      }
      setLeaveOpen(false);
      onBack();
    } catch (caught) { setError(caught.message); } finally { setStopping(false); }
  }
  const [pendingBytes, setPendingBytes] = useState(null);
  const [reviewPairs, setReviewPairs] = useState([]);
  const [reviewIndex, setReviewIndex] = useState(0);
  const [reviewDecisions, setReviewDecisions] = useState({});
  const [reviewOpen, setReviewOpen] = useState(false);
  const [preparingReview, setPreparingReview] = useState(false);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [saveFileName, setSaveFileName] = useState("");
  const [chooseLocation, setChooseLocation] = useState(false);
  const [saving, setSaving] = useState(false);
  const [exportFormat, setExportFormat] = useState("xlsx");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const sheets = useMemo(() => fileInfo?.sheets || [], [fileInfo]);
  const currentSheet = useMemo(() => sheets.find((item) => item.name === sheet) || sheets[0], [sheets, sheet]);
  const scraper = workflows[mode];

  async function inspectFile(nextFile) {
    setFile(nextFile || null); setFileInfo(null); setSheet(""); setNameColumn("");
    if (!nextFile) return;
    setLoadingFile(true);
    try {
      const form = new FormData(); form.append("file", nextFile);
      const response = await fetch(`${API}/pubmed/inspect-hcp-file`, { method: "POST", body: form });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Could not read this HCP file.");
      const first = payload.sheets?.[0];
      setFileInfo(payload); setSheet(first?.name || ""); setNameColumn(first?.columns?.[0] || "");
    } catch (caught) { setError(caught.message); } finally { setLoadingFile(false); }
  }

  async function run(event) {
    event.preventDefault(); setError(""); setMessage("");
    if (!search.trim() || !country.trim()) return setError(mode === "company" ? "Company name and country are required." : "Disease/search terms and country are required.");
    if (!account.email.trim()) return setError("Add a PubMed contact email in Account before running the scraper.");
    if (mode === "hcp_file" && (!file || !nameColumn)) return setError("Upload an HCP file and choose its clinician-name column.");
    if (activeRun.current) return;
    const active = { id: crypto.randomUUID(), controller: new AbortController() };
    activeRun.current = active;
    setRunning(true);
    try {
      const form = new FormData();
      form.append("job_id", active.id);
      form.append("mode", mode === "company" && companyTarget === "hco" ? "hco" : mode); form.append("search", search.trim()); form.append("country", country.trim()); form.append("years", String(years));
      form.append("email", account.email.trim()); form.append("api_key", account.pubmedApiKey.trim()); form.append("sheet", sheet); form.append("name_column", nameColumn); form.append("include_full_network", String(mode === "hcp_file" && fullNetwork)); form.append("rare_disease", String(rareDisease));
      if (mode === "hcp_file" && file) form.append("hcp_file", file);
      const response = await fetch(`${API}/pubmed/export`, { method: "POST", body: form, signal: active.controller.signal });
      if (!response.ok) { const payload = await response.json().catch(() => ({})); throw new Error(payload.detail || "PubMed could not complete the search."); }
      const bytes = new Uint8Array(await response.arrayBuffer());
      if (active.controller.signal.aborted) return;
      setPendingBytes(bytes);
      setSaveFileName(`pubmed_${mode}_${safeFilename(search)}_${safeFilename(country)}`);
      setChooseLocation(false);
      const reviewForm = new FormData();
      reviewForm.append("workbook", new File([bytes], "pubmed-scrape.xlsx", { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" }));
      const reviewResponse = await fetch(`${API}/pubmed/review-potential-mappings`, { method: "POST", body: reviewForm, signal: active.controller.signal });
      const reviewPayload = await reviewResponse.json();
      if (active.controller.signal.aborted) return;
      if (!reviewResponse.ok) throw new Error(reviewPayload.detail || "Could not prepare the name review.");
      if (reviewPayload.pairs?.length) {
        setReviewPairs(reviewPayload.pairs); setReviewIndex(0); setReviewDecisions({}); setReviewOpen(true);
      } else setSaveDialogOpen(true);
    } catch (caught) { if (!active.controller.signal.aborted) setError(caught.message); } finally { if (activeRun.current === active) activeRun.current = null; setRunning(false); }
  }

  async function applyNameReview() {
    if (!pendingBytes) return;
    setPreparingReview(true); setError("");
    try {
      const decisions = reviewPairs.map((pair) => ({ name_a: pair.name_a, name_b: pair.name_b, ...reviewDecisions[pair.id] }));
      const form = new FormData();
      form.append("workbook", new File([pendingBytes], "pubmed-scrape.xlsx", { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" }));
      form.append("decisions", JSON.stringify(decisions));
      const response = await fetch(`${API}/pubmed/apply-name-decisions`, { method: "POST", body: form });
      if (!response.ok) { const payload = await response.json().catch(() => ({})); throw new Error(payload.detail || "Could not apply the name decisions."); }
      setPendingBytes(new Uint8Array(await response.arrayBuffer()));
      setReviewOpen(false); setSaveDialogOpen(true);
    } catch (caught) { setError(caught.message); } finally { setPreparingReview(false); }
  }

  async function saveResults() {
    const trimmed = saveFileName.trim();
    if (!trimmed) return setError("Enter a file name.");
    if (!pendingBytes) return;
    const userFolderDirectory = account?.userFolderDirectory || account?.userDirectory || "";
    const desktopDirectory = account?.desktopDirectory || account?.desktopPath || "";
    if (window.__TAURI_INTERNALS__ && (!userFolderDirectory.trim() || !desktopDirectory.trim())) return setError("Set both User folder directory and Desktop directory in Account before exporting.");
    setSaving(true); setError("");
    const now = new Date();
    const pad = (value) => String(value).padStart(2, "0");
    const timestamp = `${pad(now.getDate())}-${pad(now.getMonth() + 1)}-${String(now.getFullYear()).slice(-2)}_${pad(now.getHours())}_${pad(now.getMinutes())}`;
    const filename = `${trimmed.replace(/\.(xlsx|csv)$/i, "")}${rareDisease ? "_RARE" : ""}_${timestamp}.${exportFormat}`;
    try {
      const form = new FormData();
      form.append("workbook", new File([pendingBytes], "pubmed.xlsx"));
      form.append("export_format", exportFormat);
      const response = await fetch(`${API}/pubmed/convert-export`, { method: "POST", body: form });
      if (!response.ok) { const payload = await response.json().catch(() => ({})); throw new Error(payload.detail || "Could not prepare the export."); }
      const bytes = new Uint8Array(await response.arrayBuffer());
      let savedPath = null;
      if (window.__TAURI_INTERNALS__) {
        const savedFiles = await invoke("save_pubmed_export", { bytes: Array.from(bytes), defaultFileName: filename, userFolderDirectory, desktopDirectory, chooseExportLocation: chooseLocation });
        if (!savedFiles) return;
        savedPath = savedFiles.exportPath;
      } else browserDownload(bytes, filename);
      setSaveDialogOpen(false); setPendingBytes(null);
      setMessage(savedPath ? `Saved to ${savedPath}` : `Saved ${filename}`);
    } catch (caught) { setError(caught instanceof Error ? caught.message : String(caught)); } finally { setSaving(false); }
  }

  return <main className="min-h-screen bg-[#f4f7fa] text-slate-950">
    <header className="border-b border-slate-700 bg-[#0c2538] text-white"><div className="mx-auto flex max-w-[1450px] items-center justify-between gap-4 px-5 py-5 lg:px-8"><div className="flex items-center gap-4"><button type="button" onClick={handleBack} className="rounded-lg p-2 text-slate-200 hover:bg-white/10" aria-label="Back to applications"><ArrowLeft size={22} /></button><div className="grid h-11 w-11 place-items-center rounded-xl bg-[#e6f8fb] text-[#087d98]"><BookOpenText size={24} /></div><div><p className="font-bold">PubMed Scraper</p><p className="text-xs text-slate-300">Search, normalize, and export publication data</p></div></div><button type="button" onClick={onAccount} className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-slate-100 hover:bg-white/10"><UserRound size={17} />Account</button></div></header>
    <div className="mx-auto max-w-[1180px] px-5 py-10 lg:px-8"><div className="mb-7"><h1 className="text-3xl font-bold tracking-tight">PubMed Scraper</h1><p className="mt-2 text-slate-500">Run the supplied PubMed extraction and normalization scrapers.</p></div><form onSubmit={run} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <label className="block text-sm font-semibold text-slate-700">Scraper</label><details className="group relative mt-2"><summary className="list-none cursor-pointer rounded-xl border border-slate-300 bg-white px-4 py-3 outline-none transition hover:border-cyan-400 [&::-webkit-details-marker]:hidden"><div className="flex items-center justify-between gap-4"><div><p className="font-semibold text-slate-950">{scraper.name}</p><p className="mt-1 text-sm font-normal text-slate-500">{scraper.description}</p></div><ChevronDown size={19} className="shrink-0 text-slate-500 transition group-open:rotate-180" /></div></summary><div className="absolute z-20 mt-2 w-full overflow-hidden rounded-xl border border-slate-200 bg-white p-1 shadow-xl">{Object.entries(workflows).map(([key, value]) => <button key={key} type="button" onClick={(event) => { setMode(key); setError(""); event.currentTarget.closest("details")?.removeAttribute("open"); }} className={`block w-full rounded-lg px-3 py-3 text-left ${key === mode ? "bg-cyan-50" : "hover:bg-slate-50"}`}><p className="font-semibold text-slate-950">{value.name}</p><p className="mt-1 text-sm text-slate-500">{value.description}</p></button>)}</div></details>
      {mode === "company" && <label className="mt-5 block text-sm font-semibold text-slate-700">What do you want to scrape?<select value={companyTarget} onChange={(event) => setCompanyTarget(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 font-normal"><option value="author">HCPs</option><option value="hco">HCOs</option></select></label>}
      <div className="mt-7 grid gap-5 md:grid-cols-2"><label className="block text-sm font-semibold text-slate-700"><span className="flex items-center gap-2"><span>{mode === "company" ? "Company name" : "Disease / search terms"}</span><span className="group relative inline-flex"><button type="button" aria-label="Help with AND and OR search conditions" aria-describedby="query-help" className="rounded-full p-1 text-slate-500 outline-none hover:bg-cyan-50 hover:text-cyan-800 focus-visible:ring-2 focus-visible:ring-cyan-500"><Info size={16} /></button><span id="query-help" role="tooltip" className="pointer-events-none absolute left-0 top-full z-30 mt-2 hidden w-[640px] max-w-[calc(100vw-3rem)] rounded-xl border border-slate-200 bg-white p-4 text-sm font-normal text-slate-700 shadow-lg group-hover:block group-focus-within:block"><span className="block text-base font-bold text-slate-950">How to write your PubMed query</span>
<span className="mt-3 block divide-y divide-slate-200">
<span className="block pb-3"><span className="block font-semibold text-slate-950">1. OR — finds either term</span><code className="mt-1 block overflow-x-auto whitespace-nowrap rounded bg-slate-50 px-2 py-1.5 text-xs">{mode === "company" ? "Revolution Medicines OR RevMed" : "Pancreatic Cancer OR PDAC"}</code><span className="mt-2 block text-xs text-slate-600">Be mindful of British vs American spelling. Use OR to include both: <code className="whitespace-nowrap font-semibold text-slate-800">Tumour OR Tumor</code></span></span>
<span className="block py-3"><span className="block font-semibold text-slate-950">2. AND — requires both terms</span><code className="mt-1 block overflow-x-auto whitespace-nowrap rounded bg-slate-50 px-2 py-1.5 text-xs">{mode === "company" ? "Boston Scientific AND Atrial Fibrilation" : "Pancreatic Cancer AND chemotherapy"}</code></span>
<span className="block pt-3"><span className="block font-semibold text-slate-950">3. AND + OR — grouped alternatives</span><span className="mt-1 block text-xs text-slate-600">Use parentheses to group alternatives.</span><code className="mt-1 block overflow-x-auto whitespace-nowrap rounded bg-slate-50 px-2 py-1.5 text-xs">{mode === "company" ? "(Revolution Medicines OR RevMed) AND (Pancreatic Cancer OR PDAC)" : "(Pancreatic Cancer OR PDAC) AND (chemotherapy OR immunotherapy)"}</code></span>
</span></span></span></span><input value={search} onChange={(event) => setSearch(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-300 px-3 py-2.5 font-normal outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100" placeholder={mode === "company" ? "e.g. Insmed" : "e.g. bronchiectasis"} /></label><label className="block text-sm font-semibold text-slate-700">Country<input value={country} onChange={(event) => setCountry(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-300 px-3 py-2.5 font-normal outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100" placeholder="e.g. Germany" /></label></div>
      {mode === "hcp_file" && <div className="mt-6 rounded-xl border border-slate-200 bg-white p-5"><p className="flex items-center gap-2 font-semibold"><FileSpreadsheet size={19} className="text-cyan-700" />HCP source file</p><input type="file" accept=".csv,.xlsx,.xls" onChange={(event) => inspectFile(event.target.files?.[0])} disabled={running || loadingFile} className="mt-4 block w-full rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600 file:mr-4 file:cursor-pointer file:rounded-lg file:border-0 file:bg-cyan-100 file:px-4 file:py-2 file:font-semibold file:text-cyan-900 hover:file:bg-cyan-200" />{loadingFile && <p className="mt-3 flex items-center gap-2 text-sm text-cyan-800"><LoaderCircle size={16} className="animate-spin" />Reading the file columns…</p>}{currentSheet && <div className="mt-4 grid gap-4 md:grid-cols-2">{sheets.length > 1 && <label className="text-sm font-semibold">Worksheet<select value={sheet} onChange={(event) => { setSheet(event.target.value); const item = sheets.find((candidate) => candidate.name === event.target.value); setNameColumn(item?.columns?.[0] || ""); }} className="mt-1.5 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-normal">{sheets.map((item) => <option key={item.name} value={item.name}>{item.name}</option>)}</select></label>}<label className="text-sm font-semibold">Clinician-name column<select value={nameColumn} onChange={(event) => setNameColumn(event.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-normal">{currentSheet.columns.map((column) => <option key={column} value={column}>{column}</option>)}</select></label></div>}</div>}
      <div className="mt-6 grid gap-3 border-t border-slate-200 pt-6">
        {mode === "hcp_file" && <button type="button" aria-pressed={fullNetwork} onClick={() => setFullNetwork((value) => !value)} disabled={running} className={`flex items-start gap-3 rounded-xl border p-4 text-left transition disabled:opacity-60 ${fullNetwork ? "border-cyan-500 bg-cyan-50" : "border-slate-300 bg-slate-50 hover:border-cyan-400"}`}><span aria-hidden="true" className={`mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded border text-sm font-bold ${fullNetwork ? "border-cyan-700 bg-cyan-700 text-white" : "border-slate-400 bg-white"}`}>{fullNetwork ? "✓" : ""}</span><span><span className="block text-sm font-semibold text-slate-900">Get the full collaborator network</span><span className="mt-1 block text-sm text-slate-500">Expand the search to publications by coauthors found through your HCP file.</span></span></button>}
        <button type="button" aria-pressed={rareDisease} onClick={() => setRareDisease((value) => !value)} disabled={running} className={`flex items-start gap-3 rounded-xl border p-4 text-left transition disabled:opacity-60 ${rareDisease ? "border-cyan-500 bg-cyan-50" : "border-slate-300 bg-slate-50 hover:border-cyan-400"}`}><span aria-hidden="true" className={`mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded border text-sm font-bold ${rareDisease ? "border-cyan-700 bg-cyan-700 text-white" : "border-slate-400 bg-white"}`}>{rareDisease ? "✓" : ""}</span><span><span className="block text-sm font-semibold text-slate-900">Rare disease</span><span className="mt-1 block text-sm text-slate-500">Keep all potentially relevant HCPs/HCOs. Clear this for non-rare diseases.</span></span></button>
      </div>
      <button type="button" onClick={() => setAdvancedOpen((value) => !value)} className="mt-6 flex items-center gap-2 text-sm font-semibold text-cyan-800">See more <ChevronDown size={16} className={advancedOpen ? "rotate-180" : ""} /></button>{advancedOpen && <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50 p-4"><label className="block max-w-sm text-sm font-semibold">Publication years<select value={years} onChange={(event) => setYears(Number(event.target.value))} className="mt-1.5 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-normal">{[1, 2, 3, 5, 7, 10, 15, 20, 30].map((value) => <option key={value} value={value}>{value} years</option>)}</select></label></div>}
      {error && <p className="mt-5 rounded-lg bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">{error}</p>}{message && <p className="mt-5 rounded-lg bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">{message}</p>}<div className="mt-7 flex justify-end"><button disabled={running} className="inline-flex items-center gap-2 rounded-xl bg-[#087d98] px-5 py-3 font-semibold text-white hover:bg-[#056b83] disabled:cursor-wait disabled:opacity-60">{running ? <><LoaderCircle size={18} className="animate-spin" />Running PubMed scraper…</> : <><Search size={18} />Run PubMed scraper</>}</button></div>
    </form></div>{reviewOpen && <ReviewNamesDialog pairs={reviewPairs} index={reviewIndex} setIndex={setReviewIndex} decisions={reviewDecisions} setDecisions={setReviewDecisions} preparing={preparingReview} onContinue={applyNameReview} onSkip={() => { setReviewOpen(false); setSaveDialogOpen(true); }} />}{saveDialogOpen && <SaveScrapeDialog fileName={saveFileName} setFileName={setSaveFileName} chooseLocation={chooseLocation} setChooseLocation={setChooseLocation} saving={saving} exportFormat={exportFormat} setExportFormat={setExportFormat} error={error} onClose={() => setSaveDialogOpen(false)} onSave={saveResults} />}
  {leaveOpen && <div className="fixed inset-0 z-[60] grid place-items-center bg-slate-950/45 p-5" role="dialog" aria-modal="true" aria-labelledby="stop-pubmed-title"><section className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl"><h2 id="stop-pubmed-title" className="text-xl font-bold">Stop the PubMed search?</h2><p className="mt-3 text-sm text-slate-600">A PubMed search is running. Going back will stop it. Would you like to leave?</p>{error && <p className="mt-3 text-sm text-rose-700">{error}</p>}<div className="mt-6 flex justify-end gap-3"><button type="button" autoFocus disabled={stopping} onClick={() => setLeaveOpen(false)} className="rounded-xl border border-slate-300 px-4 py-2.5 font-semibold disabled:opacity-50">Stay</button><button type="button" disabled={stopping} onClick={stopAndLeave} className="rounded-xl bg-rose-700 px-4 py-2.5 font-semibold text-white disabled:opacity-50">{stopping ? "Stopping…" : "Stop and leave"}</button></div></section></div>}
  </main>;
}
