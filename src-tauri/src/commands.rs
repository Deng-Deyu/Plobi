use serde::Serialize;

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
