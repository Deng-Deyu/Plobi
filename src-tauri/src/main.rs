// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod tray;

use tauri::Manager;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! Welcome to Plobi Agent.", name)
}

fn get_timestamp_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![greet, commands::get_backend_port, commands::show_main_window, commands::open_file])
        .setup(|app| {
            // Show main window on launch
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
            }
            // Setup system tray
            tray::create_tray(app)?;

            // Track overlay state with debounce
            let last_toggle = Arc::new(AtomicU64::new(0));
            let last_toggle_clone = last_toggle.clone();

            // Register Alt+/ global shortcut for overlay
            use tauri_plugin_global_shortcut::GlobalShortcutExt;
            let _ = app.global_shortcut().on_shortcut("Alt+Slash", move |app, _shortcut, _event| {
                // Debounce: prevent toggling faster than 500ms
                let now = get_timestamp_ms();
                let last = last_toggle_clone.load(Ordering::SeqCst);
                if now - last < 500 {
                    return;
                }
                last_toggle_clone.store(now, Ordering::SeqCst);

                if let Some(overlay) = app.get_webview_window("overlay") {
                    let is_visible = overlay.is_visible().unwrap_or(false);
                    if is_visible {
                        let _ = overlay.hide();
                    } else {
                        // Show and immediately set focus to prevent auto-hide
                        let _ = overlay.show();
                        std::thread::sleep(std::time::Duration::from_millis(50));
                        let _ = overlay.set_focus();
                    }
                }
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
