use serde::Serialize;
use tauri::Manager;

#[derive(Serialize)]
pub struct BackendPortResult {
    port: u16,
}

#[tauri::command]
pub fn get_backend_port() -> BackendPortResult {
    // Backend runs on 52731 by default (see plan.md §13)
    BackendPortResult {
        port: std::env::var("PLOBI_BACKEND_PORT")
            .ok()
            .and_then(|p| p.parse().ok())
            .unwrap_or(52731),
    }
}

#[tauri::command]
pub fn show_main_window(app: tauri::AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.unminimize();
        let _ = window.show();
        let _ = window.set_focus();
        let _ = window.set_ignore_cursor_events(false);
    }
}

#[tauri::command]
pub async fn open_file(path: String) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("cmd")
            .args(["/c", "start", "", &path])
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    #[cfg(target_os = "linux")]
    {
        std::process::Command::new("xdg-open")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    Ok(())
}
