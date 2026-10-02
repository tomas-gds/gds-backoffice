use std::{
    fs,
    path::{Path, PathBuf},
};
#[cfg(not(debug_assertions))]
use std::sync::Mutex;
#[cfg(not(debug_assertions))]
use tauri::Manager;
#[cfg(not(debug_assertions))]
use tauri_plugin_shell::{process::CommandChild, ShellExt};

#[cfg(not(debug_assertions))]
struct BackendProcess(Mutex<Option<CommandChild>>);

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
        .invoke_handler(tauri::generate_handler![save_csv, save_binary])
        .run(tauri::generate_context!())
        .expect("error while running Tools Workspace");
}
