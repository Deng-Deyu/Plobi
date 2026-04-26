// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod tray;

use tauri::Manager;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! Welcome to Plobi Agent.", name)
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![greet, commands::get_backend_port])
        .setup(|app| {
            // Show main window on launch
            if let Some(window) = app.get_webview_window("main") {
                window.show().unwrap();
            }
            // Setup system tray
            tray::create_tray(app)?;
            // Register Alt+/ global shortcut for overlay
            use tauri_plugin_global_shortcut::GlobalShortcutExt;
            app.global_shortcut().on_shortcut("Alt+Slash", |app, _shortcut, _event| {
                if let Some(overlay) = app.get_webview_window("overlay") {
                    if overlay.is_visible().unwrap_or(false) {
                        let _ = overlay.hide();
                    } else {
                        let _ = overlay.show();
                        let _ = overlay.set_focus();
                    }
                }
            })?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
