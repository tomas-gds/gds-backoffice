"use client";

import { useEffect, useRef, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import {
  ArrowLeft,
  Database,
  Check,
  ChevronDown,
  Download,
  FileSpreadsheet,
  FolderOpen,
  LoaderCircle,
  LockKeyhole,
  PackageOpen,
  Plus,
  RotateCcw,
  Search,
  Trash2,
  Upload,
  UserRound,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  clearLegacyAutosave,
  createProject,
  deleteProject,
  listProjects,
  loadLegacyAutosave,
  loadProjectSession,
  saveProjectSession,
  updateProject,
} from "./session-store";

const API_URL =
  import.meta.env.VITE_MATCHING_API_URL || "http://127.0.0.1:8000";

function bytesToBase64(bytes) {
  let binary = "";
  const chunkSize = 32_768;
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize));
  }
  return btoa(binary);
}

function base64ToBytes(value) {
  const binary = atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
}

async function portableFile(file) {
  if (!file) return null;
  return {
    name: file.name,
    type: file.type || "application/octet-stream",
    lastModified: file.lastModified || Date.now(),
    data: bytesToBase64(new Uint8Array(await file.arrayBuffer())),
  };
}

function restorePortableFile(portable) {
  if (!portable) return null;
  return new File([base64ToBytes(portable.data)], portable.name, {
    type: portable.type,
    lastModified: portable.lastModified,
  });
}

function fileStem(file) {
  return file?.name?.replace(/\.[^.]+$/, "") || "Dataset";
}

function exportTimestamp(date = new Date()) {
  const pad = (value) => String(value).padStart(2, "0");
  return [
    pad(date.getDate()),
    pad(date.getMonth() + 1),
    pad(date.getFullYear() % 100),
  ].join("-") + `_${pad(date.getHours())}_${pad(date.getMinutes())}`;
}

function scoreStatus(score) {
  if (score === 100) return "Exact";
  if (score >= 85) return "Strong";
  return "Review";
}

function normalizedAssignmentValue(value) {
  return String(value || "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function targetAssignmentKey(match) {
  const targetValues = (match.components || []).map(
    (component) => component.target_value,
  );
  const values = targetValues.length ? targetValues : [match.target_name];
  return values.map(normalizedAssignmentValue).join("\u001f");
}

function Badge({ children, tone = "slate" }) {
  const tones = {
    green: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    blue: "bg-blue-50 text-blue-700 ring-blue-200",
    amber: "bg-amber-50 text-amber-800 ring-amber-200",
    slate: "bg-slate-100 text-slate-600 ring-slate-200",
  };
  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-semibold ring-1 ring-inset ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

function BusyProgress({ label }) {
  return (
    <div className="mt-4" role="status" aria-live="polite">
      <div className="mb-1.5 text-sm font-medium text-cyan-800">
        <span>{label}</span>
      </div>
      <div
        role="progressbar"
        aria-label={label}
        className="h-2 overflow-hidden rounded-full bg-cyan-100"
      >
        <div className="operation-progress-indicator h-full w-1/3 rounded-full bg-cyan-600" />
      </div>
    </div>
  );
}

function FileCard({ label, file, onFile, locked = false }) {
  const input = useRef(null);
  async function chooseFile() {
    if (locked) return;
    try {
      const selected = await invoke("pick_input_file");
      if (!selected) return;
      onFile(
        new File([new Uint8Array(selected.bytes)], selected.name),
        selected.path,
      );
    } catch {
      // Browser development mode has no desktop command; use its normal picker.
      input.current?.click();
    }
  }
  return (
    <button
      onClick={chooseFile}
      className={`rounded-xl border border-dashed p-5 text-left shadow-sm transition ${locked ? "cursor-default border-slate-200 bg-slate-50" : "border-slate-300 bg-white hover:border-cyan-500 hover:bg-cyan-50/30"}`}
    >
      <input
        ref={input}
        className="hidden"
        type="file"
        accept=".csv,.xlsx,.xls"
        onChange={(event) => onFile(event.target.files?.[0] || null, null)}
      />
      <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
        {label}
      </p>
      <div className="mt-3 flex items-center justify-between gap-3">
        <div>
          <p className="max-w-[280px] truncate font-semibold">
            {file?.name || "Choose CSV or Excel file"}
          </p>
          <p className="mt-1 text-sm text-slate-500">
            {file
              ? `${(file.size / 1024).toFixed(1)} KB · ready`
              : "Processed locally by Python"}
          </p>
        </div>
        {file ? (
          locked ? <LockKeyhole className="text-slate-400" size={20} /> : <FileSpreadsheet className="text-cyan-600" />
        ) : (
          <Upload className="text-slate-400" />
        )}
      </div>
    </button>
  );
}

function MappingRow({
  pair,
  index,
  sourceColumns,
  targetColumns,
  onChange,
  onRemove,
}) {
  const fieldClass =
    "h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100";
  return (
    <div className="grid gap-3 rounded-lg border border-slate-200 bg-slate-50/70 p-3 lg:grid-cols-[1fr_1fr_150px_110px_40px] lg:items-center">
      <label>
        <span className="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400">
          {index === 0
            ? "File A · value to match"
            : "File A · supporting header"}
        </span>
        <select
          className={fieldClass}
          value={pair.source}
          onChange={(event) =>
            onChange({ ...pair, source: event.target.value })
          }
        >
          <option value="" disabled>Select a File A field</option>
          {sourceColumns.map((column) => (
            <option key={column}>{column}</option>
          ))}
        </select>
      </label>
      <label>
        <span className="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400">
          {index === 0
            ? "File B · matching value"
            : "File B · supporting header"}
        </span>
        <select
          className={fieldClass}
          value={pair.target}
          onChange={(event) =>
            onChange({ ...pair, target: event.target.value })
          }
        >
          <option value="" disabled>Select a File B field</option>
          {targetColumns.map((column) => (
            <option key={column}>{column}</option>
          ))}
        </select>
      </label>
      <label>
        <span className="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400">
          Comparison
        </span>
        <select
          className={fieldClass}
          value={pair.method}
          onChange={(event) =>
            onChange({ ...pair, method: event.target.value })
          }
        >
          <option value="similarity">Similarity</option>
          <option value="exact">Exact</option>
        </select>
      </label>
      <label>
        <span className="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400">
          Weight
        </span>
        <input
          className={fieldClass}
          min="1"
          max="100"
          type="number"
          value={pair.weight}
          onChange={(event) =>
            onChange({ ...pair, weight: Number(event.target.value) })
          }
        />
      </label>
      <Button
        aria-label="Remove field pair"
        variant="ghost"
        size="icon"
        disabled={index === 0}
        onClick={onRemove}
        className="mt-5 text-slate-400 hover:bg-rose-50 hover:text-rose-600"
      >
        <Trash2 size={16} />
      </Button>
    </div>
  );
}

export default function DatabaseMapper({ onBack, onAccount, account }) {
  const [projects, setProjects] = useState([]);
  const [activeProject, setActiveProject] = useState(null);
  const [source, setSource] = useState(null);
  const [target, setTarget] = useState(null);
  const [sourcePath, setSourcePath] = useState("");
  const [targetPath, setTargetPath] = useState("");
  const [inspection, setInspection] = useState(null);
  const [pairs, setPairs] = useState([]);
  const [result, setResult] = useState(null);
  const [decisions, setDecisions] = useState({});
  const [replacements, setReplacements] = useState({});
  const [candidateSelections, setCandidateSelections] = useState({});
  const [manualSearches, setManualSearches] = useState({});
  const [showResolution, setShowResolution] = useState(false);
  const [expandedDetails, setExpandedDetails] = useState({});
  const [openStep, setOpenStep] = useState(1);
  const [query, setQuery] = useState("");
  const [inspecting, setInspecting] = useState(false);
  const [loading, setLoading] = useState(false);
  const [leaveOpen, setLeaveOpen] = useState(false);
  const [error, setError] = useState("");
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [exportFileName, setExportFileName] = useState("");
  const [exportFormat, setExportFormat] = useState("xlsx");
  const [chooseExportLocation, setChooseExportLocation] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportMessage, setExportMessage] = useState("");
  const [checkingDuplicates, setCheckingDuplicates] = useState(false);
  const [duplicateWarning, setDuplicateWarning] = useState(null);
  const [duplicateDialogOpen, setDuplicateDialogOpen] = useState(false);
  const [duplicateResolutionDialogOpen, setDuplicateResolutionDialogOpen] = useState(false);
  const [duplicateReportLoading, setDuplicateReportLoading] = useState(false);
  const [reloadDialogOpen, setReloadDialogOpen] = useState(false);
  const [reloadingFiles, setReloadingFiles] = useState(false);
  const [restoredFiles, setRestoredFiles] = useState(null);
  const [autosaveReady, setAutosaveReady] = useState(false);
  const [autosaveStatus, setAutosaveStatus] = useState("");
  const [lastSavedAt, setLastSavedAt] = useState(null);
  const [confidenceFilter, setConfidenceFilter] = useState("all");
  const [confidenceMinimum, setConfidenceMinimum] = useState("50");
  const [confidenceMaximum, setConfidenceMaximum] = useState("75");
  const [selectedReviewIds, setSelectedReviewIds] = useState([]);
  const [resolutionConfidenceFilter, setResolutionConfidenceFilter] = useState("all");
  const [selectedResolutionIds, setSelectedResolutionIds] = useState([]);
  const [projectTransferMessage, setProjectTransferMessage] = useState("");
  const [projectTransferBusy, setProjectTransferBusy] = useState(false);
  const [newProjectDialogOpen, setNewProjectDialogOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [projectToDelete, setProjectToDelete] = useState(null);
  const [includeUnmappedTarget, setIncludeUnmappedTarget] = useState(false);
  const [confirmedDuplicateGroups, setConfirmedDuplicateGroups] = useState([]);
  const [duplicateCandidateSelections, setDuplicateCandidateSelections] = useState({});
  const [duplicateRecordResolutions, setDuplicateRecordResolutions] = useState({});
  const importProjectInput = useRef(null);
  const preservePairsOnReload = useRef(false);
  const reloadSourceInput = useRef(null);
  const reloadTargetInput = useRef(null);
  const pendingReloadSource = useRef(null);
  const activeMatchRun = useRef(null);
  const userFolderDirectory = account?.userFolderDirectory || account?.userDirectory || "";
  const desktopDirectory = account?.desktopDirectory || account?.desktopPath || "";

  useEffect(() => () => {
    const active = activeMatchRun.current;
    if (!active) return;
    active.controller.abort();
    fetch(`${API_URL}/database-mapper/cancel/${active.id}`, { method: "POST", keepalive: true }).catch(() => {});
  }, []);

  function requestProjectBack() {
    if (activeMatchRun.current) {
      setLeaveOpen(true);
    } else {
      setActiveProject(null);
    }
  }

  function stopAndLeave() {
    const active = activeMatchRun.current;
    if (active) {
      // Do not wait for the backend response: aborting this request lets the
      // running job detect the disconnect and terminate immediately.
      fetch(`${API_URL}/database-mapper/cancel/${active.id}`, {
        method: "POST",
        keepalive: true,
      }).catch(() => {});
      active.controller.abort();
      if (activeMatchRun.current === active) activeMatchRun.current = null;
    }
    setLoading(false);
    setLeaveOpen(false);
    setActiveProject(null);
  }

  const sourceDisplay = source || restoredFiles?.source;
  const targetDisplay = target || restoredFiles?.target;
  const sourceExactDuplicateRows =
    duplicateWarning?.source_exact_duplicate_rows ||
    duplicateWarning?.source_duplicate_rows ||
    0;
  const targetExactDuplicateRows =
    duplicateWarning?.target_exact_duplicate_rows ||
    duplicateWarning?.target_duplicate_rows ||
    0;
  const sourceAlmostDuplicateRows = duplicateWarning?.source_almost_duplicate_rows ?? 0;
  const targetAlmostDuplicateRows = duplicateWarning?.target_almost_duplicate_rows ?? 0;
  const hasExactDuplicateRows = sourceExactDuplicateRows > 0 || targetExactDuplicateRows > 0;
  const hasAlmostDuplicateRows = sourceAlmostDuplicateRows > 0 || targetAlmostDuplicateRows > 0;

  const matches = result?.matches || [];
  const effectiveMatches = matches.map((match) => ({
    ...match,
    ...(replacements[match.id] || {}),
  }));
  const reviewed = effectiveMatches.filter(
    (match) => (decisions[match.id] || match.decision) !== "pending",
  ).length;
  const unresolvedMatches = effectiveMatches.filter((match) => {
    const decision = decisions[match.id] || match.decision;
    return decision !== "approved" && decision !== "skipped";
  });
  const allApproved =
    effectiveMatches.length > 0 && unresolvedMatches.length === 0;
  const assignmentGroups = new Map();
  effectiveMatches.forEach((match) => {
    const decision = decisions[match.id] || match.decision;
    if (match.target_index === null || match.target_index === undefined || decision !== "approved") return;
    const key = targetAssignmentKey(match);
    if (!key.replaceAll("\u001f", "")) return;
    assignmentGroups.set(key, [...(assignmentGroups.get(key) || []), match]);
  });
  const duplicateMatchGroups = [...assignmentGroups.entries()]
    .map(([key, groupMatches]) => ({
      key,
      value: groupMatches[0]?.target_name || "Blank value",
      matches: [...groupMatches].sort((left, right) =>
        String(left.source_name || "").localeCompare(String(right.source_name || ""), undefined, { sensitivity: "base" }),
      ),
      signature: `${key}:${groupMatches.map((match) => match.id).sort().join("|")}`,
    }))
    .filter((group) => group.matches.length > 1)
    .sort((left, right) =>
      left.value.localeCompare(right.value, undefined, { sensitivity: "base" }),
    );
  const unconfirmedDuplicateGroups = duplicateMatchGroups.filter(
    (group) => !confirmedDuplicateGroups.includes(group.signature),
  );
  const duplicatesResolved = allApproved && unconfirmedDuplicateGroups.length === 0;
  const duplicateStepIsOpen = openStep === 5;
  const mappedTargetIndices = new Set(
    effectiveMatches
      .filter(
        (match) =>
          (decisions[match.id] || match.decision) === "approved" &&
          match.target_index !== null &&
          match.target_index !== undefined,
      )
      .map((match) => Number(match.target_index)),
  );
  const unmappedTargetCount = Math.max(
    0,
    (result?.target_rows || 0) - mappedTargetIndices.size,
  );
  const matchesConfidence = (match, filter, minimum, maximum) => {
    if (filter === "all") return true;
    if (filter === "none") return match.score === null || match.score === undefined;
    if (match.score === null || match.score === undefined) return false;
    const score = Number(match.score);
    if (filter === "higher") return score > Number(minimum);
    if (filter === "lower") return score < Number(minimum);
    if (filter === "between") return score >= Number(minimum) && score <= Number(maximum);
    if (filter === "95-100") return match.score >= 95;
    if (filter === "85-94") return match.score >= 85 && match.score < 95;
    if (filter === "below-85") return match.score !== null && match.score < 85;
    return false;
  };
  const filtered = effectiveMatches.filter((match) =>
    matchesConfidence(match, confidenceFilter, confidenceMinimum, confidenceMaximum) && `${match.source_name} ${match.target_name} ${(match.components || [])
      .flatMap((component) => [component.source_value, component.target_value])
      .join(" ")}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  const filteredUnresolved = unresolvedMatches.filter((match) =>
    matchesConfidence(match, resolutionConfidenceFilter),
  );
  const validPairs =
    pairs.length > 0 &&
    pairs.every((pair) => pair.source && pair.target && pair.weight > 0);
  const canRunMatching = validPairs && !checkingDuplicates;

  useEffect(() => {
    if (allApproved && unconfirmedDuplicateGroups.length > 0 && openStep !== 5) {
      setDuplicateResolutionDialogOpen(true);
    }
    if (unconfirmedDuplicateGroups.length === 0) {
      setDuplicateResolutionDialogOpen(false);
    }
  }, [allApproved, unconfirmedDuplicateGroups.length, openStep]);

  function applySession(saved) {
    setSource(saved?.sourceFile || null);
    setTarget(saved?.targetFile || null);
    setSourcePath(saved?.sourcePath || "");
    setTargetPath(saved?.targetPath || "");
    setRestoredFiles(saved?.files || null);
    setInspection(saved?.inspection || null);
    setPairs(saved?.pairs || []);
    setResult(saved?.result || null);
    setDecisions(saved?.decisions || {});
    setReplacements(saved?.replacements || {});
    setCandidateSelections(saved?.candidateSelections || {});
    setManualSearches(saved?.manualSearches || {});
    setShowResolution(Boolean(saved?.showResolution));
    setExpandedDetails(saved?.expandedDetails || {});
    setOpenStep(saved?.openStep || (saved?.result ? 3 : saved?.inspection ? 2 : 1));
    setQuery(saved?.query || "");
    setLastSavedAt(saved?.savedAt || null);
    setConfidenceFilter(["all", "higher", "lower", "between"].includes(saved?.confidenceFilter) ? saved.confidenceFilter : "all");
    setConfidenceMinimum(saved?.confidenceMinimum || "50");
    setConfidenceMaximum(saved?.confidenceMaximum || "75");
    setSelectedReviewIds([]);
    setResolutionConfidenceFilter(saved?.resolutionConfidenceFilter || "all");
    setSelectedResolutionIds([]);
    setConfirmedDuplicateGroups(saved?.confirmedDuplicateGroups || []);
    setDuplicateCandidateSelections(saved?.duplicateCandidateSelections || {});
    setDuplicateRecordResolutions(saved?.duplicateRecordResolutions || {});
    setExportFormat(saved?.exportFormat === "csv" ? "csv" : "xlsx");
    setError("");
    setExportMessage("");
  }

  useEffect(() => {
    let cancelled = false;
    async function initializeProjects() {
      try {
        let storedProjects = await listProjects();
        if (storedProjects.length === 0) {
          const legacy = await loadLegacyAutosave();
          if (legacy?.version === 1) {
            const now = legacy.savedAt || new Date().toISOString();
            const migrated = {
              id: crypto.randomUUID(),
              name: `${legacy.files?.source?.name || "File A"} ↔ ${legacy.files?.target?.name || "File B"}`,
              createdAt: now,
              updatedAt: now,
              files: legacy.files || null,
              reviewed: Object.keys(legacy.decisions || {}).length,
              total: legacy.result?.matches?.length || 0,
            };
            await createProject(migrated);
            await saveProjectSession({ ...legacy, projectId: migrated.id });
            await clearLegacyAutosave();
            storedProjects = [migrated];
          }
        }
        if (!cancelled) setProjects(storedProjects);
      } catch {
        if (!cancelled) setAutosaveStatus("Could not load projects");
      } finally {
        if (!cancelled) setAutosaveReady(true);
      }
    }
    initializeProjects();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!autosaveReady || !activeProject || (!inspection && !result && pairs.length === 0)) {
      return undefined;
    }
    const timer = window.setTimeout(async () => {
      const savedAt = new Date().toISOString();
      const fileMetadata = (file) =>
        file
          ? {
              name: file.name,
              size: file.size,
              lastModified: file.lastModified,
            }
          : null;
      try {
        const session = {
          version: 1,
          projectId: activeProject.id,
          savedAt,
          files: {
            source: fileMetadata(source) || restoredFiles?.source || null,
            target: fileMetadata(target) || restoredFiles?.target || null,
          },
          inspection,
          pairs,
          result,
          decisions,
          replacements,
          candidateSelections,
          manualSearches,
          showResolution,
          expandedDetails,
          openStep,
          query,
          confidenceFilter,
          confidenceMinimum,
          confidenceMaximum,
          resolutionConfidenceFilter,
          confirmedDuplicateGroups,
          duplicateCandidateSelections,
          duplicateRecordResolutions,
          exportFormat,
          sourceFile: source || undefined,
          targetFile: target || undefined,
          sourcePath,
          targetPath,
        };
        await saveProjectSession(session);
        const reviewedCount = (result?.matches || []).filter(
          (match) => (decisions[match.id] || match.decision) !== "pending",
        ).length;
        const nextProject = {
          ...activeProject,
          updatedAt: savedAt,
          files: session.files,
          reviewed: reviewedCount,
          total: result?.matches?.length || 0,
        };
        await updateProject(nextProject);
        setActiveProject(nextProject);
        setProjects((current) =>
          current.map((project) => project.id === nextProject.id ? nextProject : project),
        );
        setLastSavedAt(savedAt);
        setAutosaveStatus("Saved locally");
      } catch {
        setAutosaveStatus("Autosave failed");
      }
    }, 750);
    return () => window.clearTimeout(timer);
  }, [
    autosaveReady,
    activeProject?.id,
    source,
    target,
    sourcePath,
    targetPath,
    restoredFiles,
    inspection,
    pairs,
    result,
    decisions,
    replacements,
    candidateSelections,
    manualSearches,
    showResolution,
    expandedDetails,
    openStep,
    query,
    confidenceFilter,
    confidenceMinimum,
    confidenceMaximum,
    resolutionConfidenceFilter,
    confirmedDuplicateGroups,
    duplicateCandidateSelections,
    duplicateRecordResolutions,
    exportFormat,
  ]);

  async function openProject(project) {
    setAutosaveReady(false);
    try {
      const session = await loadProjectSession(project.id);
      applySession(session);
      setActiveProject(project);
      setAutosaveStatus(session ? "Project recovered" : "New project");
    } finally {
      setAutosaveReady(true);
    }
  }

  function addProject() {
    setNewProjectName(`Mapping project ${projects.length + 1}`);
    setNewProjectDialogOpen(true);
  }

  async function confirmAddProject() {
    const name = newProjectName.trim();
    if (!name) return;
    const now = new Date().toISOString();
    const project = {
      id: crypto.randomUUID(),
      name,
      createdAt: now,
      updatedAt: now,
      files: null,
      reviewed: 0,
      total: 0,
    };
    await createProject(project);
    setProjects((current) => [project, ...current]);
    applySession(null);
    setActiveProject(project);
    setAutosaveStatus("New project");
    setNewProjectDialogOpen(false);
  }

  function removeProject(project) {
    setProjectToDelete(project);
  }

  async function confirmRemoveProject() {
    if (!projectToDelete) return;
    await deleteProject(projectToDelete.id);
    setProjects((current) =>
      current.filter((item) => item.id !== projectToDelete.id),
    );
    setProjectToDelete(null);
  }

  async function exportPortableProject(project) {
    setProjectTransferBusy(true);
    setProjectTransferMessage("");
    try {
      const session = await loadProjectSession(project.id);
      if (!session) throw new Error("This project has no saved session yet.");
      const sourceFile = session.sourceFile;
      const targetFile = session.targetFile;
      if (!sourceFile || !targetFile) {
        throw new Error(
          "Open this project and attach both datasets once before exporting it.",
        );
      }
      const { sourceFile: ignoredSource, targetFile: ignoredTarget, ...sessionState } = session;
      void ignoredSource;
      void ignoredTarget;
      const portable = {
        format: "database-mapper-project",
        version: 1,
        exportedAt: new Date().toISOString(),
        project,
        session: sessionState,
        sourceFile: await portableFile(sourceFile),
        targetFile: await portableFile(targetFile),
      };
      const bytes = new TextEncoder().encode(JSON.stringify(portable));
      const fileName = `${project.name.replace(/[<>:"/\\|?*]/g, "_")}.dbmap`;
      if (window.__TAURI_INTERNALS__) {
        const savedPath = await invoke("save_binary", {
          bytes: Array.from(bytes),
          defaultFileName: fileName,
          chooseLocation: true,
        });
        if (savedPath) setProjectTransferMessage(`Project exported to ${savedPath}`);
      } else {
        const link = document.createElement("a");
        link.href = URL.createObjectURL(new Blob([bytes], { type: "application/json" }));
        link.download = fileName;
        link.click();
        URL.revokeObjectURL(link.href);
        setProjectTransferMessage(`Exported ${fileName}`);
      }
    } catch (failure) {
      setProjectTransferMessage(
        failure instanceof Error ? failure.message : "Could not export the project.",
      );
    } finally {
      setProjectTransferBusy(false);
    }
  }

  async function importPortableProject(file) {
    if (!file) return;
    setProjectTransferBusy(true);
    setProjectTransferMessage("");
    try {
      const portable = JSON.parse(await file.text());
      if (portable?.format !== "database-mapper-project" || portable?.version !== 1) {
        throw new Error("This is not a supported Database Mapper project file.");
      }
      const sourceFile = restorePortableFile(portable.sourceFile);
      const targetFile = restorePortableFile(portable.targetFile);
      if (!sourceFile || !targetFile) {
        throw new Error("The project package does not contain both datasets.");
      }
      const now = new Date().toISOString();
      const id = crypto.randomUUID();
      const project = {
        ...portable.project,
        id,
        name: `${portable.project?.name || "Imported mapping"} (Imported)`,
        createdAt: now,
        updatedAt: now,
        files: {
          source: { name: sourceFile.name, size: sourceFile.size, lastModified: sourceFile.lastModified },
          target: { name: targetFile.name, size: targetFile.size, lastModified: targetFile.lastModified },
        },
      };
      const session = {
        ...portable.session,
        projectId: id,
        savedAt: now,
        sourceFile,
        targetFile,
        files: project.files,
      };
      await createProject(project);
      await saveProjectSession(session);
      setProjects((current) => [project, ...current]);
      setProjectTransferMessage(`Imported “${project.name}”.`);
    } catch (failure) {
      setProjectTransferMessage(
        failure instanceof Error ? failure.message : "Could not import the project.",
      );
    } finally {
      setProjectTransferBusy(false);
      if (importProjectInput.current) importProjectInput.current.value = "";
    }
  }

  useEffect(() => {
    if (!source || !target || inspection) return;
    let cancelled = false;
    async function inspectFiles() {
      setInspecting(true);
      setError("");
      setResult(null);
      const body = new FormData();
      body.append("source", source);
      body.append("target", target);
      try {
        const response = await fetch(`${API_URL}/inspect-pair`, {
          method: "POST",
          body,
        });
        const data = await response.json();
        if (!response.ok)
          throw new Error(data.detail || "Could not inspect the files.");
        if (cancelled) return;
        setInspection(data);
        setOpenStep(2);
        if (!preservePairsOnReload.current) {
          setPairs([
            {
              source: "",
              target: "",
              method: "similarity",
              weight: 100,
            },
          ]);
        }
        preservePairsOnReload.current = false;
      } catch (failure) {
        if (!cancelled)
          setError(
            failure instanceof Error
              ? failure.message
              : "Could not reach the local Python service.",
          );
      } finally {
        if (!cancelled) {
          setInspecting(false);
          setReloadingFiles(false);
        }
      }
    }
    inspectFiles();
    return () => {
      cancelled = true;
    };
  }, [source, target, autosaveReady, restoredFiles, inspection]);

  function applyReloadedFiles(nextSource, nextTarget, nextSourcePath = "", nextTargetPath = "") {
    // Keep the field configuration, but clear every result and decision made
    // after pairing before asking the backend to inspect the files again.
    preservePairsOnReload.current = true;
    setReloadingFiles(true);
    setSource(nextSource);
    setTarget(nextTarget);
    setSourcePath(nextSourcePath);
    setTargetPath(nextTargetPath);
    setRestoredFiles(null);
    setInspection(null);
    setResult(null);
    setDecisions({});
    setReplacements({});
    setCandidateSelections({});
    setManualSearches({});
    setShowResolution(false);
    setExpandedDetails({});
    setQuery("");
    setConfidenceFilter("all");
    setConfidenceMinimum("50");
    setConfidenceMaximum("75");
    setResolutionConfidenceFilter("all");
    setSelectedReviewIds([]);
    setSelectedResolutionIds([]);
    setConfirmedDuplicateGroups([]);
    setDuplicateCandidateSelections({});
    setDuplicateRecordResolutions({});
    setDuplicateWarning(null);
    setDuplicateDialogOpen(false);
    setExportDialogOpen(false);
    setExportMessage("");
    setError("");
    setOpenStep(1);
  }

  async function confirmReloadFiles() {
    if (!source || !target) return;
    setReloadDialogOpen(false);
    pendingReloadSource.current = null;
    if (sourcePath && targetPath) {
      setReloadingFiles(true);
      try {
        const reloaded = await invoke("reload_input_files", {
          sourcePath,
          targetPath,
        });
        applyReloadedFiles(
          new File([new Uint8Array(reloaded.source.bytes)], reloaded.source.name),
          new File([new Uint8Array(reloaded.target.bytes)], reloaded.target.name),
          reloaded.source.path,
          reloaded.target.path,
        );
      } catch (failure) {
        setReloadingFiles(false);
        setError(
          failure instanceof Error
            ? `Could not reload the original files: ${failure.message}`
            : "Could not reload the original files. They may have been moved or deleted.",
        );
      }
      return;
    }
    reloadSourceInput.current?.click();
  }

  function selectReloadSource(file) {
    if (!file) return;
    pendingReloadSource.current = file;
    reloadTargetInput.current?.click();
  }

  function selectReloadTarget(file) {
    const nextSource = pendingReloadSource.current;
    pendingReloadSource.current = null;
    if (!nextSource || !file) return;
    applyReloadedFiles(nextSource, file);
  }

  function updatePair(index, nextPair) {
    setDuplicateWarning(null);
    setDuplicateDialogOpen(false);
    setPairs((current) =>
      current.map((pair, pairIndex) => (pairIndex === index ? nextPair : pair)),
    );
  }
  function removePair(index) {
    setDuplicateWarning(null);
    setDuplicateDialogOpen(false);
    setPairs((current) =>
      current.filter((_, pairIndex) => pairIndex !== index),
    );
  }
  function addPair() {
    setDuplicateWarning(null);
    setDuplicateDialogOpen(false);
    setPairs((current) => [
      ...current,
      {
        source: "",
        target: "",
        method: "similarity",
        weight: 20,
      },
    ]);
  }

  function recordDecision(matchId, decision) {
    setDecisions((current) => ({
      ...current,
      [matchId]: decision,
    }));
    setExpandedDetails((current) => ({
      ...current,
      [matchId]: false,
    }));
  }

  async function validateSelectedFields() {
    setCheckingDuplicates(true);
    setDuplicateWarning(null);
    setError("");
    const body = new FormData();
    body.append("source", source);
    body.append("target", target);
    body.append(
      "source_columns",
      JSON.stringify(pairs.map((pair) => pair.source)),
    );
    body.append(
      "target_columns",
      JSON.stringify(pairs.map((pair) => pair.target)),
    );

    try {
      const response = await fetch(`${API_URL}/validate-primary`, {
        method: "POST",
        body,
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Could not validate selected fields.");
      }
      if (!data.valid || data.has_almost_duplicates) {
        setDuplicateWarning(data);
        setDuplicateDialogOpen(true);
      }
      return data;
    } catch (failure) {
      setError(
        failure instanceof Error
          ? failure.message
          : "Could not validate selected fields.",
      );
      return false;
    } finally {
      setCheckingDuplicates(false);
    }
  }

  async function runMatching() {
    if (!source || !target || !canRunMatching) return;
    const duplicateCheck = await validateSelectedFields();
    if (!duplicateCheck?.valid) return;
    if (duplicateCheck.has_almost_duplicates) return;
    startMatching();
  }

  async function startMatching() {
    setDuplicateDialogOpen(false);
    setLoading(true);
    setError("");
    setResult(null);
    setDecisions({});
    setReplacements({});
    setCandidateSelections({});
    setManualSearches({});
    setConfirmedDuplicateGroups([]);
    setDuplicateCandidateSelections({});
    setDuplicateRecordResolutions({});
    setShowResolution(false);
    setExpandedDetails({});
    const body = new FormData();
    body.append("source", source);
    body.append("target", target);
    body.append("column_pairs", JSON.stringify(pairs));
    const active = { id: crypto.randomUUID(), controller: new AbortController() };
    activeMatchRun.current = active;
    body.append("job_id", active.id);
    try {
      const response = await fetch(`${API_URL}/match`, {
        method: "POST",
        body,
        signal: active.controller.signal,
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Matching failed.");
      setResult(data);
      setOpenStep(3);
    } catch (failure) {
      if (failure instanceof DOMException && failure.name === "AbortError") return;
      setError(
        failure instanceof Error
          ? failure.message
          : "Could not reach the local Python service.",
      );
    } finally {
      if (activeMatchRun.current === active) {
        activeMatchRun.current = null;
        setLoading(false);
      }
    }
  }

  async function downloadDuplicateReport(kind) {
    if (!source || !target || !validPairs) return;
    setDuplicateReportLoading(true);
    setError("");
    const body = new FormData();
    body.append("source", source);
    body.append("target", target);
    body.append(
      "source_columns",
      JSON.stringify(pairs.map((pair) => pair.source)),
    );
    body.append(
      "target_columns",
      JSON.stringify(pairs.map((pair) => pair.target)),
    );
    body.append("duplicate_kind", kind);

    try {
      const response = await fetch(`${API_URL}/duplicate-report`, {
        method: "POST",
        body,
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Could not create duplicate report.");
      }
      const blob = await response.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      const label = kind === "exact" ? "exact duplicates" : "almost duplicates";
      link.download = `${fileStem(sourceDisplay)}-${fileStem(targetDisplay)} ${label}.xlsx`;
      link.click();
      URL.revokeObjectURL(link.href);
    } catch (failure) {
      setError(
        failure instanceof Error
          ? failure.message
          : "Could not create duplicate report.",
      );
    } finally {
      setDuplicateReportLoading(false);
    }
  }

  function updateManualSearch(matchId, update) {
    setManualSearches((current) => ({
      ...current,
      [matchId]: {
        query: "",
        filters: {},
        results: [],
        selectedIndex: "",
        loading: false,
        error: "",
        ...(current[matchId] || {}),
        ...update,
      },
    }));
  }

  async function searchAllCandidates(matchId) {
    const search = manualSearches[matchId] || {};
    const filters = search.filters || {};
    const hasFilter = Object.values(filters).some((value) => value?.trim());
    if (!hasFilter || !result) return;
    if (!target) {
      updateManualSearch(matchId, {
        error: "Re-select File B in Step 1 to search the complete list.",
      });
      return;
    }

    updateManualSearch(matchId, { loading: true, error: "" });
    const body = new FormData();
    body.append("target", target);
    body.append("primary_column", result.column_pairs[0].target);
    body.append(
      "target_columns",
      JSON.stringify(result.column_pairs.map((pair) => pair.target)),
    );
    body.append("filters", JSON.stringify(filters));

    try {
      const response = await fetch(`${API_URL}/search-candidates`, {
        method: "POST",
        body,
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Could not search File B. Restart the Python Matching Engine and try again.",
        );
      }
      updateManualSearch(matchId, {
        results: data.results,
        selectedIndex: data.results[0]?.target_index ?? "",
        error: data.results.length
          ? ""
          : "No File B values contain that search text.",
      });
    } catch (failure) {
      updateManualSearch(matchId, {
        results: [],
        selectedIndex: "",
        error:
          failure instanceof Error
            ? failure.message
            : "Could not search File B.",
      });
    } finally {
      updateManualSearch(matchId, { loading: false });
    }
  }

  function selectedResolutionCandidate(match, candidatePool = null, selectionOverride = undefined) {
    const alternatives = candidatePool || (match.candidates || []).filter(
      (candidate) => candidate.target_index !== match.target_index,
    );
    const selectedIndex = selectionOverride ??
      candidateSelections[match.id] ?? alternatives[0]?.target_index ?? "__NO_MATCH__";
    if (selectedIndex === "__MANUAL_SEARCH__") {
      const search = manualSearches[match.id] || {};
      const selected = (search.results || []).find(
        (candidate) => String(candidate.target_index) === String(search.selectedIndex),
      );
      return selected
        ? {
            target_index: selected.target_index,
            target_name: selected.target_name,
            score: null,
            status: "Manual",
            reasons: [],
            components: result.column_pairs.map((pair, index) => ({
              source_column: pair.source,
              target_column: pair.target,
              source_value: match.components?.[index]?.source_value ?? "",
              target_value: selected.target_values[index] ?? "",
              method: pair.method,
              score: null,
            })),
          }
        : null;
    }
    if (selectedIndex === "__NO_MATCH__") {
      return {
        target_index: null,
        target_name: "No Match",
        score: null,
        status: "No Match",
        reasons: [],
        components: (match.components || []).map((component) => ({
          ...component,
          target_value: "No match",
          score: null,
        })),
      };
    }
    return alternatives.find(
      (candidate) => String(candidate.target_index) === String(selectedIndex),
    );
  }

  function approveResolution(match, candidatePool = null, selectionOverride = undefined) {
    const candidate = selectedResolutionCandidate(match, candidatePool, selectionOverride);
    if (!candidate) return;
    setReplacements((current) => ({
      ...current,
      [match.id]: {
        ...candidate,
        status: candidate.status || scoreStatus(candidate.score),
      },
    }));
    setDecisions((current) => ({ ...current, [match.id]: "approved" }));
  }

  function stageDuplicateResolution(group, match, candidatePool, selectionOverride, keepCurrent = false) {
    const candidate = keepCurrent
      ? null
      : selectedResolutionCandidate(match, candidatePool, selectionOverride);
    if (!keepCurrent && !candidate) return;

    const nextResolutions = {
      ...duplicateRecordResolutions,
      [match.id]: {
        groupSignature: group.signature,
        action: keepCurrent ? "keep" : "change",
        candidate,
      },
    };
    const groupComplete = group.matches.every(
      (groupMatch) => nextResolutions[groupMatch.id]?.groupSignature === group.signature,
    );

    if (!groupComplete) {
      setDuplicateRecordResolutions(nextResolutions);
      return;
    }

    setReplacements((current) => {
      const next = { ...current };
      group.matches.forEach((groupMatch) => {
        const resolution = nextResolutions[groupMatch.id];
        if (resolution?.action === "change") {
          next[groupMatch.id] = {
            ...resolution.candidate,
            status: resolution.candidate.status || scoreStatus(resolution.candidate.score),
          };
        }
      });
      return next;
    });
    setDecisions((current) => ({
      ...current,
      ...Object.fromEntries(group.matches.map((groupMatch) => [groupMatch.id, "approved"])),
    }));
    setDuplicateRecordResolutions((current) =>
      Object.fromEntries(
        Object.entries(current).filter(([, resolution]) => resolution.groupSignature !== group.signature),
      ),
    );
    // Completing every record in the group is equivalent to confirming the
    // duplicate: retain the selected assignments and remove it from review.
    setConfirmedDuplicateGroups((current) => [
      ...new Set([...current, group.signature]),
    ]);
  }

  function confirmDuplicateGroups(groups) {
    const signatures = new Set(groups.map((group) => group.signature));
    if (!signatures.size) return;

    // A confirmation accepts the current automatic/manual assignments as-is.
    // Any half-finished replacement selection is no longer relevant.
    setDuplicateRecordResolutions((current) =>
      Object.fromEntries(
        Object.entries(current).filter(
          ([, resolution]) => !signatures.has(resolution.groupSignature),
        ),
      ),
    );
    setConfirmedDuplicateGroups((current) => [
      ...new Set([...current, ...signatures]),
    ]);
  }

  function skipResolution(match) {
    setReplacements((current) => ({
      ...current,
      [match.id]: {
        target_index: null,
        target_name: "",
        score: null,
        status: "Skipped",
        reasons: [],
        components: (match.components || []).map((component) => ({
          ...component,
          target_value: "",
          score: null,
        })),
      },
    }));
    setDecisions((current) => ({ ...current, [match.id]: "skipped" }));
  }

  function buildExportData() {
    const configuredPairs = result.column_pairs;
    return {
      include_unmapped_target: includeUnmappedTarget,
      expected_unmapped_target_count: includeUnmappedTarget
        ? unmappedTargetCount
        : 0,
      headers: [
        ...configuredPairs.map(
          (pair) => `${fileStem(sourceDisplay)} - ${pair.source}`,
        ),
        ...configuredPairs.map(
          (pair) => `${fileStem(targetDisplay)} - ${pair.target}`,
        ),
      ],
      rows: effectiveMatches.map((match) => {
        const components = match.components || [];
        const skipped = (decisions[match.id] || match.decision) === "skipped";
        return [
          ...configuredPairs.map(
            (_, index) => components[index]?.source_value ?? "",
          ),
          ...configuredPairs.map((_, index) =>
            skipped ? "" : (components[index]?.target_value ?? ""),
          ),
        ];
      }),
    };
  }

  function openExportDialog() {
    if (!duplicatesResolved) return;
    setExportFileName(
      `${fileStem(sourceDisplay)}-${fileStem(targetDisplay)} Matching`,
    );
    setChooseExportLocation(false);
    setIncludeUnmappedTarget(false);
    setExportMessage("");
    setExportDialogOpen(true);
  }

  async function saveExport() {
    const trimmedName = exportFileName.trim();
    if (!trimmedName) {
      setExportMessage("Enter a file name.");
      return;
    }

    const fileName = `${trimmedName.replace(/\.(csv|xlsx)$/i, "")}_${exportTimestamp()}.${exportFormat}`;
    setExporting(true);
    setExportMessage("");

    try {
      const body = new FormData();
      body.append("export_payload", JSON.stringify(buildExportData()));
      body.append("export_format", exportFormat);
      body.append("include_unmapped_target", String(includeUnmappedTarget));
      body.append(
        "mapped_target_indices",
        JSON.stringify([...mappedTargetIndices]),
      );
      body.append(
        "target_columns",
        JSON.stringify(result.column_pairs.map((pair) => pair.target)),
      );
      body.append(
        "source_column_count",
        String(result.column_pairs.length),
      );
      if (includeUnmappedTarget && target) body.append("target", target);
      const response = await fetch(`${API_URL}/create-export`, {
        method: "POST",
        body,
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Could not create the export file.");
      }
      if (includeUnmappedTarget) {
        const appendedHeader = response.headers.get("X-Unmapped-Target-Rows");
        const appendedRows = appendedHeader === null ? null : Number(appendedHeader);
        if (appendedRows !== null && appendedRows !== unmappedTargetCount) {
          throw new Error(
            `The export included ${appendedRows.toLocaleString()} of ${unmappedTargetCount.toLocaleString()} expected unused File B rows. The file was not saved.`,
          );
        }
      }
      const exportBytes = await response.arrayBuffer();

      if (window.__TAURI_INTERNALS__) {
        if (!userFolderDirectory.trim() || !desktopDirectory.trim()) {
          throw new Error(
            "Set both User Folder Directory and Desktop Directory in Account before exporting.",
          );
        }
        const savedFiles = await invoke("save_database_mapper_export", {
          bytes: Array.from(new Uint8Array(exportBytes)),
          defaultFileName: fileName,
          userFolderDirectory,
          desktopDirectory,
          chooseExportLocation,
        });
        if (!savedFiles) return;
        setExportDialogOpen(false);
        setExportMessage(
          includeUnmappedTarget
            ? `Saved to ${savedFiles.exportPath} with ${unmappedTargetCount.toLocaleString()} unused ${targetDisplay?.name || "File B"} rows.`
            : `Saved to ${savedFiles.exportPath}`,
        );
      } else {
        const link = document.createElement("a");
        link.href = URL.createObjectURL(
          new Blob([exportBytes], {
            type:
              exportFormat === "csv"
                ? "text/csv;charset=utf-8"
                : "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          }),
        );
        link.download = fileName;
        link.click();
        URL.revokeObjectURL(link.href);
        setExportDialogOpen(false);
        setExportMessage(
          includeUnmappedTarget
            ? `Saved ${fileName} with ${unmappedTargetCount.toLocaleString()} unused File B rows.`
            : `Saved ${fileName}`,
        );
      }
    } catch (failure) {
      setExportMessage(
        failure instanceof Error ? failure.message : String(failure),
      );
    } finally {
      setExporting(false);
    }
  }

  if (!activeProject) {
    return (
      <>
      <main className="min-h-screen bg-[#f4f7fa] text-slate-950">
        <header className="border-b border-slate-200 bg-[#0c2538] text-white">
          <div className="mx-auto flex max-w-[1450px] items-center justify-between px-5 py-5 lg:px-8">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="icon"
                aria-label="Back to tools"
                onClick={onBack}
                className="text-white hover:bg-white/10 hover:text-white"
              >
                <ArrowLeft size={19} />
              </Button>
              <div className="grid h-10 w-10 place-items-center rounded-lg bg-[#e6f8fb] text-[#087d98]"><Database size={22} strokeWidth={2} /></div>
              <div>
                <p className="font-bold">Database Mapper</p>
                <p className="text-xs text-slate-300">Your mapping projects</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-300">Projects saved locally</span>
              {onAccount && <Button variant="ghost" size="sm" onClick={onAccount} className="gap-2 text-white hover:bg-white/10 hover:text-white"><UserRound size={16} />Account</Button>}
            </div>
          </div>
        </header>
        <div className="mx-auto max-w-[1450px] px-5 py-8 lg:px-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
              <p className="mt-2 text-slate-500">
                Match records between two datasets.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <input
                ref={importProjectInput}
                type="file"
                accept=".dbmap"
                className="hidden"
                onChange={(event) => importPortableProject(event.target.files?.[0])}
              />
              <Button
                variant="outline"
                disabled={projectTransferBusy}
                onClick={() => importProjectInput.current?.click()}
              >
                <PackageOpen size={17} /> Import project
              </Button>
              <Button onClick={addProject} className="bg-cyan-600 text-white hover:bg-cyan-700">
                <Plus size={17} /> New project
              </Button>
            </div>
          </div>

          {projectTransferMessage && (
            <p className="mt-5 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
              {projectTransferMessage}
            </p>
          )}

          {!autosaveReady ? (
            <p className="mt-10 flex items-center gap-2 text-slate-500">
              <LoaderCircle className="animate-spin" size={18} /> Loading projects…
            </p>
          ) : projects.length === 0 ? (
            <button
              type="button"
              onClick={addProject}
              className="mt-8 grid w-full place-items-center rounded-2xl border-2 border-dashed border-slate-300 bg-white px-6 py-16 text-center transition hover:border-cyan-500 hover:bg-cyan-50/30"
            >
              <FolderOpen className="text-cyan-600" size={38} />
              <span className="mt-4 text-lg font-bold">Create your first mapping project</span>
              <span className="mt-1 text-sm text-slate-500">Choose two files, configure the mapping, and progress will save automatically.</span>
            </button>
          ) : (
            <div className="mt-8 space-y-3">
              {projects.map((project) => {
                const progress = project.total
                  ? Math.round((project.reviewed / project.total) * 100)
                  : 0;
                return (
                  <article
                    key={project.id}
                    className="group flex w-full flex-col gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-cyan-300 hover:shadow-md lg:flex-row lg:items-center"
                  >
                    <button
                      type="button"
                      onClick={() => openProject(project)}
                      className="grid min-w-0 flex-1 gap-4 text-left lg:grid-cols-[48px_minmax(260px,1.3fr)_minmax(260px,1fr)_minmax(220px,0.8fr)] lg:items-center"
                    >
                      <div className="grid h-12 w-12 place-items-center rounded-lg bg-cyan-50 text-cyan-700">
                          <FolderOpen size={20} />
                      </div>
                      <div className="min-w-0">
                        <h2 className="truncate text-lg font-bold">{project.name}</h2>
                        <span className="mt-1 block text-xs text-slate-400">
                          Updated {new Date(project.updatedAt).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-slate-700">
                          {project.files?.source?.name || "File A not selected"}
                        </p>
                        <p className="mt-1 truncate text-sm text-slate-500">
                          {project.files?.target?.name || "File B not selected"}
                        </p>
                      </div>
                      <div className="min-w-0">
                        <div className="mb-2 flex justify-between text-xs font-medium text-slate-500">
                          <span>{project.total ? `${project.reviewed} of ${project.total} reviewed` : "Not matched yet"}</span>
                          <span>{progress}%</span>
                        </div>
                        <Progress value={progress} className="h-2" />
                      </div>
                    </button>
                    <div className="flex shrink-0 items-center justify-end gap-2 border-t border-slate-100 pt-3 lg:border-l lg:border-t-0 lg:pl-4 lg:pt-0">
                      <Button variant="ghost" size="sm" onClick={() => openProject(project)} className="text-cyan-700">
                        Open project
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={projectTransferBusy}
                        onClick={() => exportPortableProject(project)}
                        className="text-slate-600"
                      >
                        <Download size={15} /> Share
                      </Button>
                      <Button variant="ghost" size="icon" aria-label={`Delete ${project.name}`} onClick={() => removeProject(project)} className="text-slate-400 hover:bg-rose-50 hover:text-rose-600">
                        <Trash2 size={16} />
                      </Button>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>
      </main>

      {newProjectDialogOpen && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4">
          <form
            onSubmit={(event) => {
              event.preventDefault();
              confirmAddProject();
            }}
            className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-2xl"
          >
            <h2 className="text-xl font-bold">Create mapping project</h2>
            <p className="mt-1 text-sm text-slate-500">
              Give the project a name that will help you identify the two datasets.
            </p>
            <label className="mt-5 block text-sm font-semibold text-slate-700">
              Project name
              <input
                autoFocus
                value={newProjectName}
                onChange={(event) => setNewProjectName(event.target.value)}
                className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 font-normal outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100"
              />
            </label>
            <div className="mt-5 flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setNewProjectDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={!newProjectName.trim()} className="bg-cyan-600 text-white hover:bg-cyan-700">
                Create project
              </Button>
            </div>
          </form>
        </div>
      )}

      {projectToDelete && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4">
          <div role="alertdialog" aria-modal="true" className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-2xl">
            <div className="flex items-start gap-3">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-rose-100 text-rose-700">
                <Trash2 size={19} />
              </div>
              <div>
                <h2 className="text-xl font-bold">Delete project?</h2>
                <p className="mt-1 text-sm leading-6 text-slate-500">
                  “{projectToDelete.name}” and all of its locally saved progress will be permanently removed.
                </p>
              </div>
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setProjectToDelete(null)}>
                Keep project
              </Button>
              <Button onClick={confirmRemoveProject} className="bg-rose-600 text-white hover:bg-rose-700">
                Delete project
              </Button>
            </div>
          </div>
        </div>
      )}
      </>
    );
  }

  return (
    <main className="min-h-screen bg-[#f4f7fa] text-slate-950">
      <input
        ref={reloadSourceInput}
        className="hidden"
        type="file"
        accept=".csv,.xlsx,.xls"
        onChange={(event) => {
          selectReloadSource(event.target.files?.[0] || null);
          event.target.value = "";
        }}
      />
      <input
        ref={reloadTargetInput}
        className="hidden"
        type="file"
        accept=".csv,.xlsx,.xls"
        onChange={(event) => {
          selectReloadTarget(event.target.files?.[0] || null);
          event.target.value = "";
        }}
      />
      <header className="border-b border-slate-200 bg-[#0c2538] text-white">
        <div className="mx-auto flex max-w-[1450px] items-center justify-between px-5 py-4 lg:px-8">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              aria-label="Back to projects"
              onClick={requestProjectBack}
              className="text-white hover:bg-white/10 hover:text-white"
            >
              <ArrowLeft size={19} />
            </Button>
            <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#e6f8fb] text-[#087d98]"><Database size={20} strokeWidth={2} /></div>
            <div>
              <p className="text-[15px] font-bold">
                Database Mapper
              </p>
              <p className="text-xs text-slate-300">
                {activeProject.name}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 text-right">
            {(lastSavedAt || autosaveStatus) && (
              <p className="mt-0.5 text-[11px] text-slate-400">
                {lastSavedAt
                  ? `Saved locally · ${new Date(lastSavedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
                  : autosaveStatus}
              </p>
            )}
            {onAccount && <Button variant="ghost" size="sm" onClick={onAccount} className="gap-2 text-white hover:bg-white/10 hover:text-white"><UserRound size={16} />Account</Button>}
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-[1450px] space-y-5 px-5 py-6 lg:px-8">
        <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <button
            type="button"
            onClick={() => setOpenStep(openStep === 1 ? 0 : 1)}
            className="flex w-full items-center justify-between gap-4 p-5 text-left"
          >
            <div>
              <h1 className="text-xl font-bold">1. Datasets</h1>
            </div>
            <ChevronDown
              className={`shrink-0 transition-transform ${openStep === 1 ? "rotate-180" : ""}`}
              size={20}
            />
          </button>
          {openStep === 1 && (
            <div className="px-5 pb-5">
              <p className="mb-4 text-sm text-slate-500">
                Select the two datasets you want to map.
              </p>
              {inspection && source && target && (
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
                  <p className="text-sm text-slate-600">
                    Reload the current files while keeping your configured field pairs.
                  </p>
                  <Button variant="outline" size="sm" onClick={() => setReloadDialogOpen(true)} disabled={reloadingFiles || inspecting}>
                    <RotateCcw size={16} /> Reload files
                  </Button>
                </div>
              )}
              <div className="grid gap-3 lg:grid-cols-2">
                <FileCard
                  label="File A · base dataset"
                  file={sourceDisplay}
                  locked={Boolean((inspection && source && target) || reloadingFiles)}
                  onFile={(file, path) => {
                    setSource(file);
                    setSourcePath(path || "");
                    setOpenStep(1);
                  }}
                />
                <FileCard
                  label="File B · match candidates"
                  file={targetDisplay}
                  locked={Boolean((inspection && source && target) || reloadingFiles)}
                  onFile={(file, path) => {
                    setTarget(file);
                    setTargetPath(path || "");
                    setOpenStep(1);
                  }}
                />
              </div>
              {inspecting && (
                <BusyProgress label="Loading your files…" />
              )}
            </div>
          )}
        </section>

        {error && (
          <p
            role="alert"
            className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm font-medium text-rose-700"
          >
            {error}
          </p>
        )}

        {inspection && (
          <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
            <button
              type="button"
              onClick={() => setOpenStep(openStep === 2 ? 0 : 2)}
              className="flex w-full items-center justify-between gap-4 p-5 text-left"
            >
              <div>
                <h2 className="text-xl font-bold">2. Pair the fields</h2>
                {openStep !== 2 && (
                  <p className="mt-1 text-sm text-slate-500">
                    {pairs.length} configured{" "}
                    {pairs.length === 1 ? "pair" : "pairs"}
                  </p>
                )}
              </div>
              <ChevronDown
                className={`shrink-0 transition-transform ${openStep === 2 ? "rotate-180" : ""}`}
                size={20}
              />
            </button>
            {openStep === 2 && (
              <div className="px-5 pb-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <p className="text-sm text-slate-500">
                    The first pair defines the value you are actually matching
                    from File A to File B. Every additional pair is supporting
                    evidence used to improve that match; blank supporting values
                    are ignored for that record.
                  </p>
                  <div className="text-right text-xs text-slate-500">
                    <p>
                      {inspection.source.rows.toLocaleString()} source rows ·{" "}
                      {inspection.source.columns.length} headers
                    </p>
                    <p>
                      {inspection.target.rows.toLocaleString()} reference rows ·{" "}
                      {inspection.target.columns.length} headers
                    </p>
                  </div>
                </div>
                <div className="mt-4 space-y-3">
                  {pairs.map((pair, index) => (
                    <MappingRow
                      key={index}
                      pair={pair}
                      index={index}
                      sourceColumns={inspection.source.columns}
                      targetColumns={inspection.target.columns}
                      onChange={(nextPair) => updatePair(index, nextPair)}
                      onRemove={() => removePair(index)}
                    />
                  ))}
                </div>
                <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                  <Button variant="outline" onClick={addPair}>
                    <Plus size={16} /> Add supporting pair
                  </Button>
                  {!checkingDuplicates && !loading && (
                    <Button
                      disabled={!canRunMatching}
                      onClick={runMatching}
                      className="bg-cyan-600 text-white hover:bg-cyan-700 disabled:bg-slate-200"
                    >
                      <Search size={17} />
                      {duplicateWarning
                        ? "Resolve duplicate values first"
                        : "Run configured matching"}
                    </Button>
                  )}
                </div>
                {checkingDuplicates && (
                  <BusyProgress label="Checking the selected fields for duplicate combinations…" />
                )}
                {loading && (
                  <BusyProgress label="Comparing records and calculating match confidence…" />
                )}
              </div>
            )}
          </section>
        )}

        {result && (
          <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="flex flex-col gap-4 border-b border-slate-200 p-5 xl:flex-row xl:items-center xl:justify-between">
              <button
                type="button"
                onClick={() => setOpenStep(openStep === 3 ? 0 : 3)}
                className="flex flex-1 items-center justify-between gap-4 text-left"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-bold">3. Review matches</h2>
                    <Badge tone="blue">{matches.length} source rows</Badge>
                  </div>
                  <p className="mt-1 text-sm text-slate-500">
                    {openStep === 3 ? (
                      <>
                        Scored from {result.column_pairs.length} selected field{" "}
                        {result.column_pairs.length === 1 ? "pair" : "pairs"}.
                      </>
                    ) : (
                      `${reviewed} of ${matches.length} reviewed`
                    )}
                  </p>
                </div>
                <ChevronDown
                  className={`shrink-0 transition-transform ${openStep === 3 ? "rotate-180" : ""}`}
                  size={20}
                />
              </button>
              {openStep === 3 && (
                <div className="flex flex-wrap gap-2">
                  <select
                    value={confidenceFilter}
                    onChange={(event) => setConfidenceFilter(event.target.value)}
                    className="h-9 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-cyan-500"
                    aria-label="Confidence comparison"
                  >
                    <option value="all">All confidence levels</option>
                    <option value="higher">Higher than</option>
                    <option value="lower">Lower than</option>
                    <option value="between">In between</option>
                  </select>
                  {confidenceFilter !== "all" && (
                    <>
                      <select
                        value={confidenceMinimum}
                        onChange={(event) => {
                          const nextMinimum = event.target.value;
                          setConfidenceMinimum(nextMinimum);
                          if (confidenceFilter === "between" && Number(nextMinimum) > Number(confidenceMaximum)) {
                            setConfidenceMaximum(nextMinimum);
                          }
                        }}
                        className="h-9 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-cyan-500"
                        aria-label={confidenceFilter === "higher" ? "Minimum confidence" : confidenceFilter === "lower" ? "Maximum confidence" : "Lower confidence"}
                      >
                        {Array.from({ length: 21 }, (_, index) => index * 5).map((percentage) => (
                          <option key={percentage} value={percentage}>{percentage}%</option>
                        ))}
                      </select>
                      {confidenceFilter === "between" && (
                        <>
                          <span className="self-center text-sm text-slate-500">and</span>
                          <select
                            value={confidenceMaximum}
                            onChange={(event) => {
                              const nextMaximum = event.target.value;
                              setConfidenceMaximum(nextMaximum);
                              if (Number(nextMaximum) < Number(confidenceMinimum)) {
                                setConfidenceMinimum(nextMaximum);
                              }
                            }}
                            className="h-9 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-cyan-500"
                            aria-label="Upper confidence"
                          >
                            {Array.from({ length: 21 }, (_, index) => index * 5).map((percentage) => (
                              <option key={percentage} value={percentage}>{percentage}%</option>
                            ))}
                          </select>
                        </>
                      )}
                    </>
                  )}
                  <label className="relative min-w-[240px] flex-1">
                    <Search
                      className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                      size={16}
                    />
                    <input
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                      placeholder="Search results"
                      className="h-9 w-full rounded-md border border-slate-300 pl-9 pr-3 text-sm outline-none focus:border-cyan-500"
                    />
                  </label>
                </div>
              )}
            </div>
            {openStep === 3 && (
              <>
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-slate-50 px-5 py-3">
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
                    <input
                      type="checkbox"
                      checked={filtered.length > 0 && filtered.every((match) => selectedReviewIds.includes(match.id))}
                      onChange={(event) =>
                        setSelectedReviewIds((current) =>
                          event.target.checked
                            ? Array.from(new Set([...current, ...filtered.map((match) => match.id)]))
                            : current.filter((id) => !filtered.some((match) => match.id === id)),
                        )
                      }
                      className="h-4 w-4 accent-cyan-600"
                    />
                    Select all {filtered.length} filtered
                  </label>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={!selectedReviewIds.length}
                      onClick={() => {
                        selectedReviewIds.forEach((id) => recordDecision(id, "rejected"));
                        setSelectedReviewIds([]);
                      }}
                    >
                      <X size={15} /> Reject selected
                    </Button>
                    <Button
                      size="sm"
                      disabled={!selectedReviewIds.length}
                      onClick={() => {
                        selectedReviewIds.forEach((id) => recordDecision(id, "approved"));
                        setSelectedReviewIds([]);
                      }}
                      className="bg-cyan-600 text-white hover:bg-cyan-700"
                    >
                      <Check size={15} /> Approve selected
                    </Button>
                  </div>
                </div>
                <div className="divide-y divide-slate-100">
                  {filtered.map((match) => {
                    const decision = decisions[match.id] || match.decision;
                    const detailsOpen =
                      expandedDetails[match.id] ?? decision === "pending";
                    const supportingFields = (match.components || []).slice(1);
                    return (
                      <article
                        key={match.id}
                        className={`grid gap-4 p-5 lg:grid-cols-[32px_minmax(220px,1fr)_90px_minmax(220px,1fr)_200px] lg:items-center ${decision === "rejected" ? "bg-rose-50/40 opacity-70" : ""}`}
                      >
                        <input
                          type="checkbox"
                          aria-label={`Select ${match.source_name || "record"}`}
                          checked={selectedReviewIds.includes(match.id)}
                          onChange={(event) =>
                            setSelectedReviewIds((current) =>
                              event.target.checked
                                ? [...current, match.id]
                                : current.filter((id) => id !== match.id),
                            )
                          }
                          className="h-4 w-4 accent-cyan-600"
                        />
                        <div>
                          <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                            {fileStem(sourceDisplay)}
                          </p>
                          <p className="mt-1 font-bold">
                            {match.source_name || "Blank value"}
                          </p>
                          {supportingFields.length > 0 && (
                            <button
                              type="button"
                              onClick={() =>
                                setExpandedDetails((current) => ({
                                  ...current,
                                  [match.id]: !detailsOpen,
                                }))
                              }
                              className="mt-1 inline-flex items-center gap-1 text-sm font-medium text-cyan-700 hover:text-cyan-900"
                            >
                              Details
                              <ChevronDown
                                size={15}
                                className={`transition-transform ${detailsOpen ? "rotate-180" : ""}`}
                              />
                            </button>
                          )}
                        </div>
                        <div className="flex items-center gap-3 lg:flex-col">
                          <div
                            className={`grid h-12 w-12 place-items-center rounded-full text-sm font-extrabold ${match.status === "No Match" ? "bg-slate-100 text-slate-600" : match.score >= 85 ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-800"}`}
                          >
                            {match.score === null ? "—" : `${match.score}%`}
                          </div>
                          <Badge
                            tone={
                              match.status === "Exact"
                                ? "green"
                                : match.status === "Strong"
                                  ? "blue"
                                  : match.status === "No Match"
                                    ? "slate"
                                    : "amber"
                            }
                          >
                            {match.status}
                          </Badge>
                        </div>
                        <div>
                          <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                            {fileStem(targetDisplay)}
                          </p>
                          <p className="mt-1 font-bold">{match.target_name}</p>
                        </div>
                        <div className="flex items-center gap-2 lg:justify-end">
                          {decision === "pending" ? (
                            <>
                              <Button
                                aria-label="Reject match"
                                variant="outline"
                                size="icon"
                                onClick={() =>
                                  recordDecision(match.id, "rejected")
                                }
                              >
                                <X size={17} />
                              </Button>
                              <Button
                                onClick={() =>
                                  recordDecision(match.id, "approved")
                                }
                                className="bg-cyan-600 text-white hover:bg-cyan-700"
                              >
                                <Check size={16} /> Approve
                              </Button>
                            </>
                          ) : (
                            <>
                              <Badge
                                tone={
                                  decision === "approved" ? "green" : "slate"
                                }
                              >
                                {decision}
                              </Badge>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() =>
                                  recordDecision(match.id, "pending")
                                }
                              >
                                Undo
                              </Button>
                            </>
                          )}
                        </div>
                        {detailsOpen && supportingFields.length > 0 && (
                          <div className="grid grid-cols-2 gap-x-6 gap-y-3 pt-1 lg:col-span-5 lg:grid-cols-[32px_minmax(220px,1fr)_90px_minmax(220px,1fr)_200px]">
                            {supportingFields.map((field, fieldIndex) => (
                              <div
                                key={`${field.source_column}-${field.target_column}-${fieldIndex}`}
                                className="col-span-2 grid grid-cols-2 gap-6 lg:col-span-4 lg:col-start-2 lg:grid-cols-[minmax(220px,1fr)_90px_minmax(220px,1fr)]"
                              >
                                <div>
                                  <p className="text-xs font-semibold text-slate-400">
                                    {field.source_column}
                                  </p>
                                  <p className="mt-0.5 text-sm text-slate-700">
                                    {field.source_value || "—"}
                                  </p>
                                </div>
                                <div className="hidden lg:block" />
                                <div>
                                  <p className="text-xs font-semibold text-slate-400">
                                    {field.target_column}
                                  </p>
                                  <p className="mt-0.5 text-sm text-slate-700">
                                    {field.target_value || "—"}
                                  </p>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </article>
                    );
                  })}
                </div>
                <div className="border-t border-slate-200 bg-slate-50 p-5">
                  <div className="mb-2 flex justify-between text-sm">
                    <span className="font-medium">Review progress</span>
                    <span className="font-bold">
                      {reviewed} of {matches.length}
                    </span>
                  </div>
                  <Progress
                    value={
                      matches.length ? (reviewed / matches.length) * 100 : 0
                    }
                    className="h-2"
                  />
                  {!allApproved && (
                    <div className="mt-4 flex justify-end">
                      <Button
                        onClick={() => {
                          setShowResolution(true);
                          setOpenStep(4);
                        }}
                        className="bg-cyan-600 text-white hover:bg-cyan-700"
                      >
                        Resolve {unresolvedMatches.length} unmatched{" "}
                        {unresolvedMatches.length === 1 ? "record" : "records"}
                      </Button>
                    </div>
                  )}
                </div>
              </>
            )}
          </section>
        )}

        {result && showResolution && (
          <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <button
              type="button"
              onClick={() => setOpenStep(openStep === 4 ? 0 : 4)}
              className="flex w-full items-center justify-between gap-4 p-5 text-left"
            >
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold">
                    4. Resolve unmatched records
                  </h2>
                  <Badge tone={allApproved ? "green" : "amber"}>
                    {unresolvedMatches.length} remaining
                  </Badge>
                </div>
                <p className="mt-1 text-sm text-slate-500">
                  Choose a different candidate and verify its supporting fields.
                </p>
              </div>
              <ChevronDown
                className={`shrink-0 transition-transform ${openStep === 4 ? "rotate-180" : ""}`}
                size={20}
              />
            </button>

            {openStep === 4 && !allApproved && (
              <div className="border-t border-slate-200">
                  <>
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-slate-50 px-5 py-3">
                    <div className="flex flex-wrap items-center gap-3">
                      <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
                        <input
                          type="checkbox"
                          checked={filteredUnresolved.length > 0 && filteredUnresolved.every((match) => selectedResolutionIds.includes(match.id))}
                          onChange={(event) =>
                            setSelectedResolutionIds((current) =>
                              event.target.checked
                                ? Array.from(new Set([...current, ...filteredUnresolved.map((match) => match.id)]))
                                : current.filter((id) => !filteredUnresolved.some((match) => match.id === id)),
                            )
                          }
                          className="h-4 w-4 accent-cyan-600"
                        />
                        Select all {filteredUnresolved.length} filtered
                      </label>
                      <select
                        value={resolutionConfidenceFilter}
                        onChange={(event) => setResolutionConfidenceFilter(event.target.value)}
                        className="h-9 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-cyan-500"
                        aria-label="Filter unresolved records by confidence"
                      >
                        <option value="all">All confidence levels</option>
                        <option value="95-100">95–100%</option>
                        <option value="85-94">85–94%</option>
                        <option value="below-85">Below 85%</option>
                        <option value="none">No confidence</option>
                      </select>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={!selectedResolutionIds.length}
                        onClick={() => {
                          unresolvedMatches.filter((match) => selectedResolutionIds.includes(match.id)).forEach(skipResolution);
                          setSelectedResolutionIds([]);
                        }}
                      >
                        Skip selected
                      </Button>
                      <Button
                        size="sm"
                        disabled={!selectedResolutionIds.length}
                        onClick={() => {
                          unresolvedMatches.filter((match) => selectedResolutionIds.includes(match.id)).forEach(approveResolution);
                          setSelectedResolutionIds([]);
                        }}
                        className="bg-cyan-600 text-white hover:bg-cyan-700"
                      >
                        <Check size={15} /> Approve selected
                      </Button>
                    </div>
                  </div>
                  <div className="divide-y divide-slate-100">
                    {filteredUnresolved.map((match) => {
                      const alternatives = (match.candidates || []).filter(
                        (candidate) =>
                          candidate.target_index !== match.target_index,
                      );
                      const selectedIndex =
                        candidateSelections[match.id] ??
                        alternatives[0]?.target_index ??
                        "__NO_MATCH__";
                      const noMatchSelected = selectedIndex === "__NO_MATCH__";
                      const manualSearchSelected =
                        selectedIndex === "__MANUAL_SEARCH__";
                      const manualSearch = manualSearches[match.id] || {
                        query: "",
                        filters: {},
                        results: [],
                        selectedIndex: "",
                        loading: false,
                        error: "",
                      };
                      const selectedManualResult = manualSearch.results.find(
                        (candidate) =>
                          String(candidate.target_index) ===
                          String(manualSearch.selectedIndex),
                      );
                      const manualCandidate = selectedManualResult
                        ? {
                            target_index: selectedManualResult.target_index,
                            target_name: selectedManualResult.target_name,
                            score: null,
                            status: "Manual",
                            reasons: [],
                            components: result.column_pairs.map(
                              (pair, index) => ({
                                source_column: pair.source,
                                target_column: pair.target,
                                source_value:
                                  match.components?.[index]?.source_value ?? "",
                                target_value:
                                  selectedManualResult.target_values[index] ??
                                  "",
                                method: pair.method,
                                score: null,
                              }),
                            ),
                          }
                        : null;
                      const selectedCandidate = manualSearchSelected
                        ? manualCandidate
                        : noMatchSelected
                          ? {
                              target_index: null,
                              target_name: "No Match",
                              score: null,
                              status: "No Match",
                              reasons: [],
                              components: (match.components || []).map(
                                (component) => ({
                                  ...component,
                                  target_value: "No match",
                                  score: null,
                                }),
                              ),
                            }
                          : alternatives.find(
                              (candidate) =>
                                String(candidate.target_index) ===
                                String(selectedIndex),
                            );
                      const supportingFields = (
                        selectedCandidate?.components || []
                      ).slice(1);

                      return (
                        <article key={match.id} className="p-5">
                          <div className="grid gap-4 lg:grid-cols-[minmax(260px,1fr)_minmax(340px,1.2fr)_auto] lg:items-start">
                            <div>
                              <p className="flex h-5 items-center text-xs font-bold uppercase tracking-wider text-slate-400">
                                {fileStem(sourceDisplay)}
                              </p>
                              <div className="mt-1 flex h-10 items-center gap-3">
                                <input
                                  type="checkbox"
                                  aria-label={`Select ${match.source_name || "record"}`}
                                  checked={selectedResolutionIds.includes(match.id)}
                                  onChange={(event) =>
                                    setSelectedResolutionIds((current) =>
                                      event.target.checked
                                        ? [...current, match.id]
                                        : current.filter((id) => id !== match.id),
                                    )
                                  }
                                  className="h-4 w-4 shrink-0 accent-cyan-600"
                                />
                                <p className="font-bold">
                                  {match.source_name || "Blank value"}
                                </p>
                              </div>
                            </div>
                            <label className="block text-sm font-semibold text-slate-700">
                              <span className="flex h-5 items-center">Other candidates</span>
                              <select
                                value={selectedIndex}
                                onChange={(event) =>
                                  setCandidateSelections((current) => ({
                                    ...current,
                                    [match.id]: event.target.value,
                                  }))
                                }
                                className="mt-1 h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm font-normal outline-none focus:border-cyan-500"
                              >
                                {alternatives.map((candidate) => (
                                  <option
                                    key={candidate.target_index}
                                    value={candidate.target_index}
                                  >
                                    {candidate.target_name} — {candidate.score}%
                                  </option>
                                ))}
                                <option value="__MANUAL_SEARCH__">
                                  Manual Search
                                </option>
                                <option value="__NO_MATCH__">No Match</option>
                              </select>
                            </label>
                            <div className="mt-6 flex h-10 gap-2">
                            <Button
                              variant="outline"
                              onClick={() => skipResolution(match)}
                            >
                              Skip
                            </Button>
                            <Button
                              disabled={!selectedCandidate}
                              onClick={() => approveResolution(match)}
                              className="bg-cyan-600 text-white hover:bg-cyan-700 disabled:bg-slate-200"
                            >
                              <Check size={16} />{" "}
                              {noMatchSelected
                                ? "Confirm no match"
                                : manualSearchSelected
                                  ? "Approve manual match"
                                  : "Approve candidate"}
                            </Button>
                            </div>
                          </div>

                          {manualSearchSelected && (
                            <div className="mt-4 rounded-lg border border-cyan-200 bg-cyan-50/40 p-4">
                              <div className="flex flex-wrap items-start justify-between gap-3">
                                <div>
                                  <p className="text-sm font-semibold text-slate-700">
                                    Search the complete {fileStem(targetDisplay)} list
                                  </p>
                                  <p className="mt-1 text-xs text-slate-500">
                                    Fill one or more fields. Multiple filters must all match the same File B row.
                                  </p>
                                </div>
                                <Button
                                  variant="outline"
                                  disabled={
                                    manualSearch.loading ||
                                    !Object.values(manualSearch.filters || {}).some((value) => value?.trim())
                                  }
                                  onClick={() => searchAllCandidates(match.id)}
                                >
                                  {manualSearch.loading ? (
                                    <LoaderCircle
                                      className="animate-spin"
                                      size={16}
                                    />
                                  ) : (
                                    <Search size={16} />
                                  )}
                                  Search all File B
                                </Button>
                              </div>

                              <div className="mt-4 px-4 py-4">
                                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                                  {fileStem(sourceDisplay)} record
                                </p>
                                <div className="mt-3 grid gap-x-8 gap-y-4 sm:grid-cols-2 xl:grid-cols-4">
                                  {result.column_pairs.map((pair, index) => (
                                    <div key={pair.source}>
                                      <p className="text-xs font-semibold text-slate-400">{pair.source}</p>
                                      <p className="mt-1 text-sm font-medium text-slate-900">
                                        {match.components?.[index]?.source_value || "—"}
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              </div>

                              <div className="mt-4 rounded-lg border border-slate-200 bg-slate-100 p-4">
                                <div className="flex items-center gap-2">
                                  <Search size={15} className="text-slate-500" />
                                  <p className="text-xs font-bold uppercase tracking-wider text-slate-600">
                                    Filter {fileStem(targetDisplay)}
                                  </p>
                                </div>
                                <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                                  {result.column_pairs.map((pair) => (
                                    <label key={pair.target} className="block">
                                      <span className="mb-1 block text-xs font-semibold text-slate-600">{pair.target}</span>
                                      <input
                                        value={manualSearch.filters?.[pair.target] || ""}
                                        onChange={(event) =>
                                          updateManualSearch(match.id, {
                                            filters: {
                                              ...(manualSearch.filters || {}),
                                              [pair.target]: event.target.value,
                                            },
                                          })
                                        }
                                        onKeyDown={(event) => {
                                          if (event.key === "Enter" && !manualSearch.loading) {
                                            searchAllCandidates(match.id);
                                          }
                                        }}
                                        placeholder={`Filter ${pair.target}`}
                                        className="h-9 w-full rounded-md border border-slate-300 bg-white px-3 text-sm shadow-sm outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100"
                                      />
                                    </label>
                                  ))}
                                </div>
                              </div>

                              {manualSearch.loading && (
                                <BusyProgress label="Searching the complete File B dataset…" />
                              )}

                              {manualSearch.results.length > 0 && (
                                <div className="mt-4">
                                  <div className="mb-2 flex items-center justify-between">
                                    <p className="text-sm font-semibold text-slate-700">Search results</p>
                                    <p className="text-xs text-slate-500">{manualSearch.results.length} found · scroll for more</p>
                                  </div>
                                  <div className="max-h-[485px] overflow-auto rounded-lg border border-slate-200 bg-white">
                                    <table className="w-full border-collapse text-left text-sm">
                                      <thead className="sticky top-0 z-10 bg-slate-100 text-xs uppercase tracking-wide text-slate-500">
                                        <tr>
                                          <th className="w-10 px-3 py-3">Select</th>
                                          {result.column_pairs.map((pair) => (
                                            <th key={pair.target} className="min-w-[170px] px-3 py-3">{pair.target}</th>
                                          ))}
                                        </tr>
                                      </thead>
                                      <tbody className="divide-y divide-slate-100">
                                        {manualSearch.results.map((candidate) => (
                                          <tr
                                            key={candidate.target_index}
                                            onClick={() => updateManualSearch(match.id, { selectedIndex: candidate.target_index })}
                                            className={`cursor-pointer hover:bg-cyan-50 ${String(manualSearch.selectedIndex) === String(candidate.target_index) ? "bg-cyan-50" : ""}`}
                                          >
                                            <td className="px-3 py-3">
                                              <input
                                                type="radio"
                                                name={`manual-result-${match.id}`}
                                                checked={String(manualSearch.selectedIndex) === String(candidate.target_index)}
                                                onChange={() => updateManualSearch(match.id, { selectedIndex: candidate.target_index })}
                                                className="h-4 w-4 accent-cyan-600"
                                              />
                                            </td>
                                            {result.column_pairs.map((pair, index) => (
                                              <td key={pair.target} className="px-3 py-3 text-slate-700">
                                                {candidate.target_values[index] || "—"}
                                              </td>
                                            ))}
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </div>
                              )}

                              {manualSearch.error && (
                                <p className="mt-3 text-sm font-medium text-amber-800">
                                  {manualSearch.error}
                                </p>
                              )}
                            </div>
                          )}

                          {selectedCandidate && !manualSearchSelected && (
                            <div className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 border-t border-slate-100 pt-4">
                              <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                                {fileStem(sourceDisplay)}
                              </p>
                              <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                                {fileStem(targetDisplay)}
                                {selectedCandidate.score !== null &&
                                  ` · ${selectedCandidate.score}%`}
                              </p>
                              {supportingFields.map((field, fieldIndex) => (
                                <div
                                  key={`${field.source_column}-${field.target_column}-${fieldIndex}`}
                                  className="col-span-2 grid grid-cols-2 gap-6"
                                >
                                  <div>
                                    <p className="text-xs font-semibold text-slate-400">
                                      {field.source_column}
                                    </p>
                                    <p className="mt-0.5 text-sm text-slate-700">
                                      {field.source_value || "—"}
                                    </p>
                                  </div>
                                  <div>
                                    <p className="text-xs font-semibold text-slate-400">
                                      {field.target_column}
                                    </p>
                                    <p className="mt-0.5 text-sm text-slate-700">
                                      {field.target_value || "—"}
                                    </p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </article>
                      );
                    })}
                  </div>
                  </>
              </div>
            )}
          </section>
        )}

        {result && allApproved && unconfirmedDuplicateGroups.length > 0 && (
          <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <button
              type="button"
              onClick={() => setOpenStep(duplicateStepIsOpen ? 0 : 5)}
              className="flex w-full items-center justify-between gap-4 p-5 text-left"
            >
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold">5. Resolve duplicate matches</h2>
                  <Badge tone={unconfirmedDuplicateGroups.length ? "amber" : "green"}>
                    {unconfirmedDuplicateGroups.length} remaining
                  </Badge>
                </div>
                <p className="mt-1 text-sm text-slate-500">
                  Review cases where different File A values map to the same File B value.
                </p>
              </div>
              <ChevronDown
                className={`shrink-0 transition-transform ${duplicateStepIsOpen ? "rotate-180" : ""}`}
                size={20}
              />
            </button>

            {duplicateStepIsOpen && (
              <div className="space-y-4 border-t border-slate-200 bg-slate-50 p-5">
                {unconfirmedDuplicateGroups.map((group) => {
                  const confirmed = false;
                  return (
                    <div key={group.signature} className="overflow-hidden rounded-xl border border-slate-200 bg-white">
                      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-amber-50 px-4 py-3">
                        <div>
                          <p className="text-xs font-bold uppercase tracking-wider text-amber-700">File B value</p>
                          <p className="mt-0.5 font-bold text-slate-900">{group.value}</p>
                          <p className="mt-0.5 text-xs text-slate-600">
                            {group.matches.length} different File A values use this match
                          </p>
                        </div>
                        {confirmed ? (
                          <div className="flex items-center gap-2">
                            <Badge tone="green">Confirmed duplicate</Badge>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setConfirmedDuplicateGroups((current) => current.filter((signature) => signature !== group.signature))}
                            >
                              Reopen
                            </Button>
                          </div>
                        ) : (
                          <Button
                            size="sm"
                            onClick={() => {
                              confirmDuplicateGroups([group]);
                            }}
                            className="bg-amber-600 text-white hover:bg-amber-700"
                          >
                            <Check size={15} /> Confirm duplicate
                          </Button>
                        )}
                      </div>

                      <div className="divide-y divide-slate-100">
                        {group.matches.map((match) => {
                          const alternatives = (match.candidates || []).filter(
                            (candidate) => targetAssignmentKey(candidate) !== group.key,
                          );
                          const currentCandidate = {
                            target_index: match.target_index,
                            target_name: match.target_name,
                            score: match.score,
                            reasons: match.reasons || [],
                            components: match.components || [],
                          };
                          const candidateOptions = [currentCandidate, ...alternatives];
                          const selectedIndex = duplicateCandidateSelections[match.id] ?? currentCandidate.target_index ?? "__NO_MATCH__";
                          const noMatchSelected = selectedIndex === "__NO_MATCH__";
                          const manualSearchSelected = selectedIndex === "__MANUAL_SEARCH__";
                          const manualSearch = manualSearches[match.id] || { filters: {}, results: [], selectedIndex: "", loading: false, error: "" };
                          const selectedCandidate = selectedResolutionCandidate(match, candidateOptions, selectedIndex);
                          const currentMatchSelected = String(selectedIndex) === String(currentCandidate.target_index);
                          const supportingFields = (selectedCandidate?.components || []).slice(1);
                          const stagedResolution =
                            duplicateRecordResolutions[match.id]?.groupSignature === group.signature
                              ? duplicateRecordResolutions[match.id]
                              : null;

                          return (
                            <article key={match.id} className="p-4">
                              {stagedResolution ? (
                                <div className="flex flex-wrap items-center justify-between gap-4 rounded-lg bg-emerald-50 px-4 py-3">
                                  <div>
                                    <p className="text-xs font-bold uppercase tracking-wider text-slate-400">{fileStem(sourceDisplay)}</p>
                                    <p className="mt-1 font-bold">{match.source_name || "Blank value"}</p>
                                    <p className="mt-1 text-sm font-medium text-emerald-700">
                                      {stagedResolution.action === "keep"
                                        ? `Keep current match: ${match.target_name}`
                                        : `Change to: ${stagedResolution.candidate?.target_name || "No Match"}`}
                                    </p>
                                  </div>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => setDuplicateRecordResolutions((current) => {
                                      const next = { ...current };
                                      delete next[match.id];
                                      return next;
                                    })}
                                  >
                                    Edit
                                  </Button>
                                </div>
                              ) : (
                                <>
                              <div className="grid gap-4 lg:grid-cols-[minmax(260px,1fr)_minmax(340px,1.2fr)_auto] lg:items-end">
                                <div>
                                  <p className="text-xs font-bold uppercase tracking-wider text-slate-400">{fileStem(sourceDisplay)}</p>
                                  <p className="mt-1 font-bold">{match.source_name || "Blank value"}</p>
                                </div>
                                <label className="block text-sm font-semibold text-slate-700">
                                  Current File B match
                                  <select
                                    value={selectedIndex}
                                    onChange={(event) => setDuplicateCandidateSelections((current) => ({ ...current, [match.id]: event.target.value }))}
                                    className="mt-1 h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm font-normal outline-none focus:border-cyan-500"
                                  >
                                    <option value={currentCandidate.target_index}>
                                      Current: {currentCandidate.target_name} — {currentCandidate.score}%
                                    </option>
                                    {alternatives.map((candidate) => (
                                      <option key={candidate.target_index} value={candidate.target_index}>
                                        {candidate.target_name} — {candidate.score}%
                                      </option>
                                    ))}
                                    <option value="__MANUAL_SEARCH__">Manual Search</option>
                                    <option value="__NO_MATCH__">No Match</option>
                                  </select>
                                </label>
                                <div className="flex h-10 gap-2">
                                  <Button
                                    variant="outline"
                                    onClick={() => stageDuplicateResolution(group, match, candidateOptions, selectedIndex, true)}
                                  >
                                    Keep current
                                  </Button>
                                  <Button
                                    disabled={!selectedCandidate || currentMatchSelected}
                                    onClick={() => stageDuplicateResolution(group, match, candidateOptions, selectedIndex)}
                                    className="bg-cyan-600 text-white hover:bg-cyan-700 disabled:bg-slate-200"
                                  >
                                    <Check size={16} /> {noMatchSelected ? "Confirm no match" : manualSearchSelected ? "Approve manual match" : "Change match"}
                                  </Button>
                                </div>
                              </div>

                              {manualSearchSelected && (
                                <div className="mt-4 rounded-lg border border-cyan-200 bg-cyan-50/40 p-4">
                                  <div className="flex flex-wrap items-start justify-between gap-3">
                                    <div>
                                      <p className="text-sm font-semibold text-slate-700">Search the complete {fileStem(targetDisplay)} list</p>
                                      <p className="mt-1 text-xs text-slate-500">Fill one or more fields. Multiple filters must all match the same File B row.</p>
                                    </div>
                                    <Button
                                      variant="outline"
                                      disabled={manualSearch.loading || !Object.values(manualSearch.filters || {}).some((value) => value?.trim())}
                                      onClick={() => searchAllCandidates(match.id)}
                                    >
                                      <Search size={16} /> Search all File B
                                    </Button>
                                  </div>

                                  <div className="mt-4 px-4 py-4">
                                    <p className="text-xs font-bold uppercase tracking-wider text-slate-500">{fileStem(sourceDisplay)} record</p>
                                    <div className="mt-3 grid gap-x-8 gap-y-4 sm:grid-cols-2 xl:grid-cols-4">
                                      {result.column_pairs.map((pair, index) => (
                                        <div key={pair.source}>
                                          <p className="text-xs font-semibold text-slate-400">{pair.source}</p>
                                          <p className="mt-1 text-sm font-medium text-slate-900">{match.components?.[index]?.source_value || "—"}</p>
                                        </div>
                                      ))}
                                    </div>
                                  </div>

                                  <div className="mt-4 rounded-lg border border-slate-200 bg-slate-100 p-4">
                                    <p className="text-xs font-bold uppercase tracking-wider text-slate-600">Filter {fileStem(targetDisplay)}</p>
                                    <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                                      {result.column_pairs.map((pair) => (
                                        <label key={pair.target} className="block">
                                          <span className="mb-1 block text-xs font-semibold text-slate-600">{pair.target}</span>
                                          <input
                                            value={manualSearch.filters?.[pair.target] || ""}
                                            onChange={(event) => updateManualSearch(match.id, { filters: { ...(manualSearch.filters || {}), [pair.target]: event.target.value } })}
                                            onKeyDown={(event) => { if (event.key === "Enter" && !manualSearch.loading) searchAllCandidates(match.id); }}
                                            placeholder={`Filter ${pair.target}`}
                                            className="h-9 w-full rounded-md border border-slate-300 bg-white px-3 text-sm shadow-sm outline-none focus:border-cyan-500"
                                          />
                                        </label>
                                      ))}
                                    </div>
                                  </div>

                                  {manualSearch.loading && <BusyProgress label="Searching the complete File B dataset…" />}
                                  {manualSearch.results.length > 0 && (
                                    <div className="mt-4 max-h-[485px] overflow-auto rounded-lg border border-slate-200 bg-white">
                                      <table className="w-full border-collapse text-left text-sm">
                                        <thead className="sticky top-0 z-10 bg-slate-100 text-xs uppercase tracking-wide text-slate-500">
                                          <tr><th className="w-10 px-3 py-3">Select</th>{result.column_pairs.map((pair) => <th key={pair.target} className="min-w-[170px] px-3 py-3">{pair.target}</th>)}</tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-100">
                                          {manualSearch.results.map((candidate) => (
                                            <tr key={candidate.target_index} onClick={() => updateManualSearch(match.id, { selectedIndex: candidate.target_index })} className="cursor-pointer hover:bg-cyan-50">
                                              <td className="px-3 py-3"><input type="radio" name={`duplicate-manual-${match.id}`} checked={String(manualSearch.selectedIndex) === String(candidate.target_index)} onChange={() => updateManualSearch(match.id, { selectedIndex: candidate.target_index })} className="h-4 w-4 accent-cyan-600" /></td>
                                              {result.column_pairs.map((pair, index) => <td key={pair.target} className="px-3 py-3 text-slate-700">{candidate.target_values[index] || "—"}</td>)}
                                            </tr>
                                          ))}
                                        </tbody>
                                      </table>
                                    </div>
                                  )}
                                  {manualSearch.error && <p className="mt-3 text-sm font-medium text-amber-800">{manualSearch.error}</p>}
                                </div>
                              )}

                              {selectedCandidate && !manualSearchSelected && (
                                <div className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 border-t border-slate-100 pt-4">
                                  <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                                    {fileStem(sourceDisplay)}
                                  </p>
                                  <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                                    {fileStem(targetDisplay)}
                                    {selectedCandidate.score !== null && ` · ${selectedCandidate.score}%`}
                                  </p>
                                  {supportingFields.map((field, fieldIndex) => (
                                    <div
                                      key={`${field.source_column}-${field.target_column}-${fieldIndex}`}
                                      className="col-span-2 grid grid-cols-2 gap-6"
                                    >
                                      <div>
                                        <p className="text-xs font-semibold text-slate-400">{field.source_column}</p>
                                        <p className="mt-0.5 text-sm text-slate-700">{field.source_value || "—"}</p>
                                      </div>
                                      <div>
                                        <p className="text-xs font-semibold text-slate-400">{field.target_column}</p>
                                        <p className="mt-0.5 text-sm text-slate-700">{field.target_value || "—"}</p>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                                </>
                              )}
                            </article>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        )}

        {result && duplicatesResolved && (
          <section className="flex flex-col gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-xl font-bold">Export results</h2>
              <p className="mt-1 text-sm text-slate-500">
                Download the completed mapping as an Excel workbook or CSV file. {unmappedTargetCount.toLocaleString()} File B rows are not currently mapped.
              </p>
            </div>
            <Button
              onClick={openExportDialog}
              className="shrink-0 bg-[#0c2538] text-white hover:bg-[#163d58]"
            >
              <Download size={15} /> Export results
            </Button>
          </section>
        )}

        {exportMessage && !exportDialogOpen && (
          <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-700">
            {exportMessage}
          </p>
        )}
      </div>

      {duplicateResolutionDialogOpen && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4" role="presentation">
          <div role="alertdialog" aria-modal="true" aria-labelledby="duplicate-resolution-title" className="w-full max-w-2xl rounded-xl bg-white p-6 shadow-2xl">
            <div className="flex items-start gap-3">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-amber-100 text-amber-800">!</div>
              <div>
                <h2 id="duplicate-resolution-title" className="text-xl font-bold">Duplicate matches found</h2>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  {unconfirmedDuplicateGroups.length} {unconfirmedDuplicateGroups.length === 1 ? "File B value is" : "File B values are"} currently assigned to more than one File A record.
                </p>
              </div>
            </div>
            <p className="mt-4 text-sm text-slate-600">
              You can keep every current assignment and continue to download, or review the current matches individually in Step 5.
            </p>
            <div className="mt-6 flex flex-wrap justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  confirmDuplicateGroups(unconfirmedDuplicateGroups);
                  setDuplicateResolutionDialogOpen(false);
                  setOpenStep(0);
                }}
              >
                Skip and continue to download
              </Button>
              <Button
                onClick={() => {
                  setDuplicateResolutionDialogOpen(false);
                  setOpenStep(5);
                }}
                className="bg-amber-600 text-white hover:bg-amber-700"
              >
                Resolve duplicates
              </Button>
            </div>
          </div>
        </div>
      )}

      {reloadDialogOpen && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4" role="presentation">
          <div role="alertdialog" aria-modal="true" aria-labelledby="reload-files-title" className="w-full max-w-3xl rounded-xl bg-white p-6 shadow-2xl">
            <div className="flex items-start gap-3">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-amber-100 text-amber-800">
                <RotateCcw size={20} />
              </div>
              <div>
                <h2 id="reload-files-title" className="text-xl font-bold">Reload both files?</h2>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  {sourcePath && targetPath
                    ? "The app will reread the same File A and File B from their original locations."
                    : "You will select File A and File B once; future reloads can use their original locations automatically."} Your configured field pairs will be kept; matching results, approvals, manual selections, duplicate decisions, and export progress will be reset.
                </p>
              </div>
            </div>
            <div className="mt-6 flex flex-wrap justify-end gap-2">
              <Button variant="outline" onClick={() => setReloadDialogOpen(false)}>Cancel</Button>
              <Button onClick={confirmReloadFiles} className="bg-amber-600 text-white hover:bg-amber-700">
                <RotateCcw size={16} /> Reload files and reset results
              </Button>
            </div>
          </div>
        </div>
      )}

      {duplicateDialogOpen && duplicateWarning && (
        <div
          className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4"
          role="presentation"
        >
          <div
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="duplicate-dialog-title"
            className="w-full max-w-4xl rounded-xl bg-white p-6 shadow-2xl"
          >
            <div className="flex items-start gap-3">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-amber-100 text-amber-800">
                <span className="text-xl font-bold">!</span>
              </div>
              <div>
                <h2 id="duplicate-dialog-title" className="text-xl font-bold">
                  Review duplicate mapping values
                </h2>
                <p className="mt-1 text-sm leading-6 text-slate-500">
                  The selected mapping fields are checked in two ways: exact
                  character-for-character duplicates, and duplicates created
                  only after normalisation (accents, capitalization, punctuation,
                  and spacing are ignored).
                </p>
              </div>
            </div>

            {hasExactDuplicateRows && <section className="mt-5 overflow-hidden rounded-lg border border-amber-200 bg-amber-50">
              <div className="border-b border-amber-200 bg-amber-100 px-4 py-3">
                <h3 className="font-bold text-amber-950">Exact duplicates</h3>
                <p className="mt-1 text-sm text-amber-900">
                  The selected mapping values are identical character-for-character. These must be corrected before matching can start.
                </p>
              </div>
              <div className="grid divide-y divide-amber-200 sm:grid-cols-2 sm:divide-x sm:divide-y-0">
                <div className="p-4">
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-400">{fileStem(sourceDisplay)}</p>
                  <p className="mt-1 text-2xl font-bold text-slate-900">{sourceExactDuplicateRows.toLocaleString()}</p>
                  <p className="text-xs text-slate-500">exact duplicate rows</p>
                </div>
                <div className="p-4">
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-400">{fileStem(targetDisplay)}</p>
                  <p className="mt-1 text-2xl font-bold text-slate-900">{targetExactDuplicateRows.toLocaleString()}</p>
                  <p className="text-xs text-slate-500">exact duplicate rows</p>
                </div>
              </div>
              {hasExactDuplicateRows && <div className="border-t border-amber-200 bg-amber-50 px-4 py-3"><Button size="sm" variant="outline" disabled={duplicateReportLoading} onClick={() => downloadDuplicateReport("exact")}>{duplicateReportLoading ? <LoaderCircle className="animate-spin" size={16} /> : <Download size={16} />}Download exact duplicates</Button></div>}
            </section>}

            {hasAlmostDuplicateRows && <section className="mt-4 overflow-hidden rounded-lg border border-sky-200">
              <div className="border-b border-sky-200 bg-sky-50 px-4 py-3">
                <h3 className="font-bold text-sky-950">Almost duplicates</h3>
                <p className="mt-1 text-sm text-sky-900">
                  These values become identical only after normalisation. They are warnings and do not block matching.
                </p>
              </div>
              <div className="grid divide-y divide-slate-200 sm:grid-cols-2 sm:divide-x sm:divide-y-0">
                <div className="p-4">
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-400">{fileStem(sourceDisplay)}</p>
                  <p className="mt-1 text-2xl font-bold text-slate-900">{sourceAlmostDuplicateRows.toLocaleString()}</p>
                  <p className="text-xs text-slate-500">almost duplicate rows</p>
                </div>
                <div className="p-4">
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-400">{fileStem(targetDisplay)}</p>
                  <p className="mt-1 text-2xl font-bold text-slate-900">{targetAlmostDuplicateRows.toLocaleString()}</p>
                  <p className="text-xs text-slate-500">almost duplicate rows</p>
                </div>
              </div>
              {hasAlmostDuplicateRows && <div className="border-t border-sky-200 bg-white px-4 py-3"><Button size="sm" variant="outline" disabled={duplicateReportLoading} onClick={() => downloadDuplicateReport("almost")}>{duplicateReportLoading ? <LoaderCircle className="animate-spin" size={16} /> : <Download size={16} />}Download almost duplicates</Button></div>}
            </section>}

            {hasExactDuplicateRows ? (
              <p className="mt-4 text-sm text-amber-800">Exact duplicates were found. Matching is blocked until they are corrected or different mapping fields are selected.</p>
            ) : (
              <p className="mt-4 text-sm text-slate-600">No exact duplicates were found. You may continue matching.</p>
            )}

            {duplicateReportLoading && (
              <BusyProgress label="Creating the duplicate-values workbook…" />
            )}

            <div className="mt-5 flex flex-wrap justify-end gap-2">
              <Button variant="outline" disabled={duplicateReportLoading} onClick={() => setDuplicateDialogOpen(false)}>
                Cancel
              </Button>
              {!hasExactDuplicateRows && (
                <Button disabled={duplicateReportLoading} onClick={startMatching} className="bg-cyan-600 text-white hover:bg-cyan-700">
                  Continue matching
                </Button>
              )}
            </div>
          </div>
        </div>
      )}

      {exportDialogOpen && (
        <div
          className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget && !exporting) {
              setExportDialogOpen(false);
            }
          }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="export-dialog-title"
            className="w-full max-w-2xl rounded-xl bg-white p-6 shadow-2xl"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 id="export-dialog-title" className="text-xl font-bold">
                  Export matching file
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  Choose an export format and file name. The export will be saved to Desktop/GDS Backoffice/Database Mapper.
                </p>
              </div>
              <Button
                aria-label="Close export dialog"
                variant="ghost"
                size="icon"
                disabled={exporting}
                onClick={() => setExportDialogOpen(false)}
              >
                <X size={18} />
              </Button>
            </div>

            <fieldset className="mt-5">
              <legend className="text-sm font-semibold text-slate-700">
                Export format
              </legend>
              <div className="mt-2 grid gap-3 sm:grid-cols-2">
                <label
                  className={`cursor-pointer rounded-lg border p-3 transition ${
                    exportFormat === "xlsx"
                      ? "border-cyan-600 bg-cyan-50 ring-1 ring-cyan-600"
                      : "border-slate-200 bg-white hover:border-slate-300"
                  }`}
                >
                  <input
                    type="radio"
                    name="export-format"
                    value="xlsx"
                    checked={exportFormat === "xlsx"}
                    onChange={() => setExportFormat("xlsx")}
                    className="sr-only"
                  />
                  <span className="block text-sm font-semibold text-slate-800">
                    Excel workbook (.xlsx)
                  </span>
                </label>
                <label
                  className={`cursor-pointer rounded-lg border p-3 transition ${
                    exportFormat === "csv"
                      ? "border-cyan-600 bg-cyan-50 ring-1 ring-cyan-600"
                      : "border-slate-200 bg-white hover:border-slate-300"
                  }`}
                >
                  <input
                    type="radio"
                    name="export-format"
                    value="csv"
                    checked={exportFormat === "csv"}
                    onChange={() => setExportFormat("csv")}
                    className="sr-only"
                  />
                  <span className="block text-sm font-semibold text-slate-800">
                    CSV file (.csv)
                  </span>
                </label>
              </div>
            </fieldset>

            <label className="mt-5 block text-sm font-semibold text-slate-700">
              File name
              <input
                autoFocus
                value={exportFileName}
                onChange={(event) => setExportFileName(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !exporting) saveExport();
                }}
                className="mt-1 h-10 w-full rounded-md border border-slate-300 px-3 text-sm font-normal outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100"
              />
            </label>

            <label className="mt-3 flex w-fit cursor-pointer items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={chooseExportLocation}
                onChange={(event) =>
                  setChooseExportLocation(event.target.checked)
                }
                className="h-4 w-4 accent-cyan-600"
              />
              <span>Choose a different save location</span>
            </label>

            {unmappedTargetCount > 0 && (
              <label className="mt-3 flex w-fit cursor-pointer items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={includeUnmappedTarget}
                  onChange={(event) =>
                    setIncludeUnmappedTarget(event.target.checked)
                  }
                  className="h-4 w-4 accent-cyan-600"
                />
                <span>
                  Include {unmappedTargetCount.toLocaleString()} unused {targetDisplay?.name || "File B"} rows
                </span>
              </label>
            )}

            {exportMessage && (
              <p className="mt-3 text-sm font-medium text-rose-700">
                {exportMessage}
              </p>
            )}

            {exporting && (
              <BusyProgress label={`Creating and saving the ${exportFormat === "csv" ? "CSV" : "Excel"} file…`} />
            )}

            <div className="mt-5 flex justify-end gap-2">
              <Button
                variant="outline"
                disabled={exporting}
                onClick={() => setExportDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button
                disabled={exporting || !exportFileName.trim()}
                onClick={saveExport}
                className="bg-[#0c2538] text-white hover:bg-[#163d58] disabled:bg-slate-300"
              >
                {exporting ? (
                  <LoaderCircle className="animate-spin" size={16} />
                ) : (
                  <Download size={16} />
                )}
                Save export
              </Button>
            </div>
          </div>
        </div>
      )}

      {leaveOpen && (
        <div className="fixed inset-0 z-[60] grid place-items-center bg-slate-950/45 p-5" role="dialog" aria-modal="true" aria-labelledby="stop-matching-title">
          <section className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
            <h2 id="stop-matching-title" className="text-xl font-bold">Stop matching?</h2>
            <p className="mt-3 text-sm text-slate-600">Matching is running. Going back will stop it. Would you like to leave?</p>
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="outline" autoFocus onClick={() => setLeaveOpen(false)}>Stay</Button>
              <Button onClick={stopAndLeave} className="bg-rose-700 text-white hover:bg-rose-800">Stop and leave</Button>
            </div>
          </section>
        </div>
      )}

    </main>
  );
}
