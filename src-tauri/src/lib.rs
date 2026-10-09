use std::{
    fs,
    path::{Path, PathBuf},
};
use serde::Serialize;
#[cfg(not(debug_assertions))]
use std::sync::Mutex;
#[cfg(not(debug_assertions))]
use tauri::Manager;
#[cfg(not(debug_assertions))]
use tauri_plugin_shell::{process::CommandChild, ShellExt};

#[cfg(not(debug_assertions))]
struct BackendProcess(Mutex<Option<CommandChild>>);

#[derive(Serialize)]
struct LoadedInputFile {
    path: String,
    name: String,
    bytes: Vec<u8>,
}

#[derive(Serialize)]
struct ReloadedInputFiles {
    source: LoadedInputFile,
    target: LoadedInputFile,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct SavedDatabaseMapperExport {
    export_path: String,
}

fn load_input_file(path: PathBuf) -> Result<LoadedInputFile, String> {
    let name = path
        .file_name()
        .and_then(|value| value.to_str())
        .ok_or_else(|| "The selected file does not have a valid name.".to_string())?
        .to_string();
    let bytes = fs::read(&path)
        .map_err(|error| format!("Could not read {}: {error}", path.display()))?;
    Ok(LoadedInputFile {
        path: path.display().to_string(),
        name,
        bytes,
    })
}

#[tauri::command]
async fn pick_input_file() -> Result<Option<LoadedInputFile>, String> {
    tauri::async_runtime::spawn_blocking(|| {
        let selected = rfd::FileDialog::new()
            .add_filter("Data files", &["csv", "xlsx", "xls"])
            .pick_file();
        selected.map(load_input_file).transpose()
    })
    .await
    .map_err(|error| error.to_string())?
}

#[tauri::command]
async fn reload_input_files(
    source_path: String,
    target_path: String,
) -> Result<ReloadedInputFiles, String> {
    tauri::async_runtime::spawn_blocking(move || {
        Ok(ReloadedInputFiles {
            source: load_input_file(PathBuf::from(source_path))?,
            target: load_input_file(PathBuf::from(target_path))?,
        })
    })
    .await
    .map_err(|error| error.to_string())?
}

fn unused_path(folder: &Path, file_name: &str, number_before_name: bool) -> PathBuf {
    let requested = folder.join(file_name);
    if !requested.exists() {
        return requested;
    }

    let path = Path::new(file_name);
    let stem = path
        .file_stem()
        .and_then(|value| value.to_str())
        .unwrap_or("Matching");
    let extension = path
        .extension()
        .and_then(|value| value.to_str())
        .unwrap_or("csv");
    for number in 1..10_000 {
        let candidate_name = if number_before_name {
            format!("{number} - {stem}.{extension}")
        } else {
            format!("{stem} ({number}).{extension}")
        };
        let candidate = folder.join(candidate_name);
        if !candidate.exists() {
            return candidate;
        }
    }
    requested
}

#[tauri::command]
async fn save_csv(
    csv: String,
    default_file_name: String,
    choose_location: bool,
) -> Result<Option<String>, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let requested_name = Path::new(&default_file_name)
            .file_name()
            .and_then(|name| name.to_str())
            .unwrap_or("FileA-FileB Matching.csv");
        let safe_name: String = requested_name
            .chars()
            .map(|character| {
                if character.is_control()
                    || matches!(
                        character,
                        '<' | '>' | ':' | '"' | '/' | '\\' | '|' | '?' | '*'
                    )
                {
                    '_'
                } else {
                    character
                }
            })
            .collect();
        let safe_name = safe_name.trim_matches(&[' ', '.'][..]);
        let safe_name = if safe_name.is_empty() {
            "FileA-FileB Matching"
        } else {
            safe_name
        };
        let file_name = if safe_name.to_lowercase().ends_with(".csv") {
            safe_name.to_string()
        } else {
            format!("{safe_name}.csv")
        };

        let path: Option<PathBuf> = if choose_location {
            rfd::FileDialog::new()
                .add_filter("CSV file", &["csv"])
                .set_file_name(&file_name)
                .save_file()
        } else {
            let folder = dirs::download_dir()
                .or_else(dirs::document_dir)
                .ok_or_else(|| "Could not find the Downloads or Documents folder.".to_string())?;
            Some(unused_path(&folder, &file_name, false))
        };

        match path {
            Some(path) => {
                fs::write(&path, csv).map_err(|error| error.to_string())?;
                Ok(Some(path.display().to_string()))
            }
            None => Ok(None),
        }
    })
    .await
    .map_err(|error| error.to_string())?
}

#[tauri::command]
async fn save_binary(
    bytes: Vec<u8>,
    default_file_name: String,
    choose_location: bool,
    number_before_name: Option<bool>,
) -> Result<Option<String>, String> {
    tauri::async_runtime::spawn_blocking(move || {
        if bytes.is_empty() {
            return Err("The file is empty.".to_string());
        }

        let requested_name = Path::new(&default_file_name)
            .file_name()
            .and_then(|name| name.to_str())
            .unwrap_or("FileA-FileB Matching.xlsx");
        let safe_name: String = requested_name
            .chars()
            .map(|character| {
                if character.is_control()
                    || matches!(
                        character,
                        '<' | '>' | ':' | '"' | '/' | '\\' | '|' | '?' | '*'
                    )
                {
                    '_'
                } else {
                    character
                }
            })
            .collect();
        let safe_name = safe_name.trim_matches(&[' ', '.'][..]);
        let safe_name = if safe_name.is_empty() {
            "FileA-FileB Matching"
        } else {
            safe_name
        };
        let is_project = safe_name.to_lowercase().ends_with(".dbmap");
        let is_csv = safe_name.to_lowercase().ends_with(".csv");
        let file_name = if is_project || is_csv || safe_name.to_lowercase().ends_with(".xlsx") {
            safe_name.to_string()
        } else {
            format!("{safe_name}.xlsx")
        };

        let path: Option<PathBuf> = if choose_location {
            let dialog = rfd::FileDialog::new().set_file_name(&file_name);
            if is_project {
                dialog.add_filter("Database Mapper project", &["dbmap"]).save_file()
            } else if is_csv {
                dialog.add_filter("CSV file", &["csv"]).save_file()
            } else {
                dialog.add_filter("Excel workbook", &["xlsx"]).save_file()
            }
        } else {
            let folder = dirs::download_dir()
                .or_else(dirs::document_dir)
                .ok_or_else(|| "Could not find the Downloads or Documents folder.".to_string())?;
            Some(unused_path(&folder, &file_name, number_before_name.unwrap_or(false)))
        };

        match path {
            Some(path) => {
                fs::write(&path, bytes).map_err(|error| error.to_string())?;
                Ok(Some(path.display().to_string()))
            }
            None => Ok(None),
        }
    })
    .await
    .map_err(|error| error.to_string())?
}

#[tauri::command]
async fn save_database_mapper_export(
    bytes: Vec<u8>,
    default_file_name: String,
    user_folder_directory: String,
    desktop_directory: String,
) -> Result<SavedDatabaseMapperExport, String> {
    tauri::async_runtime::spawn_blocking(move || {
        if bytes.is_empty() {
            return Err("The file is empty.".to_string());
        }

        let requested_name = Path::new(&default_file_name)
            .file_name()
            .and_then(|name| name.to_str())
            .unwrap_or("FileA-FileB Matching.xlsx");
        let safe_name: String = requested_name
            .chars()
            .map(|character| {
                if character.is_control()
                    || matches!(
                        character,
                        '<' | '>' | ':' | '"' | '/' | '\\' | '|' | '?' | '*'
                    )
                {
                    '_'
                } else {
                    character
                }
            })
            .collect();
        let safe_name = safe_name.trim_matches(&[' ', '.'][..]);
        let file_name = if safe_name.to_lowercase().ends_with(".csv")
            || safe_name.to_lowercase().ends_with(".xlsx")
        {
            safe_name.to_string()
        } else {
            format!("{safe_name}.xlsx")
        };

        let backup_folder = PathBuf::from(user_folder_directory.trim()).join("Database Mapper");
        let export_folder = PathBuf::from(desktop_directory.trim())
            .join("GDS Backoffice")
            .join("Database Mapper");
        fs::create_dir_all(&backup_folder)
            .map_err(|error| format!("Could not create the Database Mapper backup folder: {error}"))?;
        fs::create_dir_all(&export_folder)
            .map_err(|error| format!("Could not create the Desktop Database Mapper folder: {error}"))?;

        let backup_path = unused_path(&backup_folder, &file_name, false);
        fs::write(&backup_path, &bytes)
            .map_err(|error| format!("Could not save the Database Mapper backup: {error}"))?;

        let export_path = unused_path(&export_folder, &file_name, false);
        fs::write(&export_path, bytes)
            .map_err(|error| format!("Could not save the Desktop export: {error}"))?;

        Ok(SavedDatabaseMapperExport {
            export_path: export_path.display().to_string(),
        })
    })
    .await
    .map_err(|error| error.to_string())?
}

#[tauri::command]
async fn save_pubmed_export(
    bytes: Vec<u8>,
    default_file_name: String,
    user_folder_directory: String,
    desktop_directory: String,
    choose_export_location: bool,
) -> Result<Option<SavedDatabaseMapperExport>, String> {
    tauri::async_runtime::spawn_blocking(move || {
        if bytes.is_empty() {
            return Err("The file is empty.".to_string());
        }

        let requested_name = Path::new(&default_file_name)
            .file_name()
            .and_then(|name| name.to_str())
            .unwrap_or("PubMed.xlsx");
        let safe_name: String = requested_name
            .chars()
            .map(|character| {
                if character.is_control()
                    || matches!(
                        character,
                        '<' | '>' | ':' | '"' | '/' | '\\' | '|' | '?' | '*'
                    )
                {
                    '_'
                } else {
                    character
                }
            })
            .collect();
        let safe_name = safe_name.trim_matches(&[' ', '.'][..]);
        let file_name = if safe_name.to_lowercase().ends_with(".csv")
            || safe_name.to_lowercase().ends_with(".xlsx")
        {
            safe_name.to_string()
        } else {
            format!("{safe_name}.xlsx")
        };

        if user_folder_directory.trim().is_empty() || desktop_directory.trim().is_empty() {
            return Err("Set both User folder directory and Desktop directory in Account.".into());
        }
        if user_folder_directory.contains('\"') || user_folder_directory.contains('\'') || desktop_directory.contains('\"') || desktop_directory.contains('\'') {
            return Err("Remove quotation marks from the directories in Account.".into());
        }
        let backup_folder = PathBuf::from(user_folder_directory.trim()).join("PubMed Scraper");
        let export_folder = PathBuf::from(desktop_directory.trim())
            .join("GDS Backoffice")
            .join("PubMed Scraper");
        fs::create_dir_all(&backup_folder)
            .map_err(|error| format!("Could not create the PubMed Scraper backup folder: {error}"))?;
        fs::create_dir_all(&export_folder)
            .map_err(|error| format!("Could not create the Desktop PubMed Scraper folder: {error}"))?;

        let export_path = if choose_export_location {
            let dialog = rfd::FileDialog::new().set_directory(&export_folder).set_file_name(&file_name);
            let selected = if file_name.to_lowercase().ends_with(".csv") { dialog.add_filter("CSV file", &["csv"]).save_file() } else { dialog.add_filter("Excel workbook", &["xlsx"]).save_file() };
            match selected { Some(path) => path, None => return Ok(None) }
        } else { unused_path(&export_folder, &file_name, false) };

        let backup_path = unused_path(&backup_folder, &file_name, false);
        fs::write(&backup_path, &bytes)
            .map_err(|error| format!("Could not save the PubMed Scraper backup: {error}"))?;

        fs::write(&export_path, bytes)
            .map_err(|error| format!("Could not save the Desktop export: {error}"))?;

        Ok(Some(SavedDatabaseMapperExport {
            export_path: export_path.display().to_string(),
        }))
    })
    .await
    .map_err(|error| error.to_string())?
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|_app| {
            #[cfg(not(debug_assertions))]
            {
                let (mut events, child) = _app
                    .shell()
                    .sidecar("database-mapper-engine")
                    ?
                    .spawn()?;
                _app.manage(BackendProcess(Mutex::new(Some(child))));
                tauri::async_runtime::spawn(async move {
                    while events.recv().await.is_some() {}
                });
            }
            Ok(())
        })
        .on_window_event(|_window, _event| {
            #[cfg(not(debug_assertions))]
            if matches!(_event, tauri::WindowEvent::Destroyed) {
                if let Ok(mut process) = _window.state::<BackendProcess>().0.lock() {
                    if let Some(mut child) = process.take() {
                        let _ = child.kill();
                    }
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            save_csv,
            save_binary,
            save_database_mapper_export,
            save_pubmed_export,
            pick_input_file,
            reload_input_files,
        ])
        .run(tauri::generate_context!())
        .expect("error while running Tools Workspace");
}
