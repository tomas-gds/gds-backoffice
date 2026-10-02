import { execFileSync } from "node:child_process";
import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { join, resolve } from "node:path";

if (process.platform !== "win32") {
  throw new Error("The distributable sidecar must be built on Windows.");
}

const root = resolve(import.meta.dirname, "..");
const python = join(root, "backend", ".venv", "Scripts", "python.exe");

if (!existsSync(python)) {
  throw new Error(
    "backend\\.venv is missing. Create it with: py -3.12 -m venv backend\\.venv",
  );
}

execFileSync(
  python,
  [
    "-m",
    "PyInstaller",
    "--noconfirm",
    "--clean",
    "--onefile",
    "--name",
    "database-mapper-engine",
    "--distpath",
    join(root, "backend", "dist-sidecar"),
    "--workpath",
    join(root, "backend", "build-sidecar"),
    "--specpath",
    join(root, "backend"),
    "--paths",
    root,
    "--collect-all",
    "python_calamine",
    "--collect-all",
    "Bio",
    "--collect-all",
    "babel",
    "--collect-all",
    "pycountry",
    join(root, "backend", "sidecar.py"),
  ],
  { cwd: root, stdio: "inherit" },
);

const targetTriple = execFileSync("rustc", ["--print", "host-tuple"], {
  encoding: "utf8",
}).trim();
if (!targetTriple) throw new Error("Could not determine the Rust target triple.");

const binaryDirectory = join(root, "src-tauri", "binaries");
mkdirSync(binaryDirectory, { recursive: true });
copyFileSync(
  join(root, "backend", "dist-sidecar", "database-mapper-engine.exe"),
  join(binaryDirectory, `database-mapper-engine-${targetTriple}.exe`),
);

console.log(`Prepared Database Mapper engine for ${targetTriple}.`);
