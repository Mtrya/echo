use std::sync::Mutex;
use tauri::{Emitter, Manager};
use tauri_plugin_shell::ShellExt;

struct SidecarState {
    child: Option<tauri_plugin_shell::process::CommandChild>,
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_shell::init())
        .manage(Mutex::new(SidecarState { child: None }))
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            let handle = app.handle().clone();

            // Find an available port
            let port = find_available_port(8000, 10);
            log::info!("Using port {} for backend sidecar", port);

            // Spawn the sidecar
            let sidecar = handle
                .shell()
                .sidecar("echo-backend")
                .expect("failed to create sidecar command")
                .args(["--port", &port.to_string(), "--tauri"]);

            let (mut rx, child) = sidecar.spawn().expect("failed to spawn sidecar");

            // Store the child process for cleanup
            let state = handle.state::<Mutex<SidecarState>>();
            state.lock().unwrap().child = Some(child);

            // Log sidecar output in background
            tauri::async_runtime::spawn(async move {
                use tauri_plugin_shell::process::CommandEvent;
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => {
                            let line = String::from_utf8_lossy(&line);
                            log::info!("[sidecar] {}", line);
                        }
                        CommandEvent::Stderr(line) => {
                            let line = String::from_utf8_lossy(&line);
                            log::warn!("[sidecar] {}", line);
                        }
                        CommandEvent::Terminated(status) => {
                            log::info!("[sidecar] terminated with status: {:?}", status);
                            break;
                        }
                        _ => {}
                    }
                }
            });

            // Poll health endpoint until backend is ready
            let poll_handle = handle.clone();
            tauri::async_runtime::spawn(async move {
                let url = format!("http://127.0.0.1:{}/health", port);
                let client = reqwest::Client::new();

                for i in 0..60 {
                    match client.get(&url).send().await {
                        Ok(resp) if resp.status().is_success() => {
                            log::info!("Backend ready on port {} (attempt {})", port, i + 1);
                            let _ = poll_handle.emit("backend-ready", port);
                            return;
                        }
                        _ => {
                            tokio::time::sleep(std::time::Duration::from_millis(500)).await;
                        }
                    }
                }
                log::error!("Backend failed to start within 30 seconds");
            });

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                let state = window.state::<Mutex<SidecarState>>();
                let mut guard = state.lock().unwrap();
                if let Some(child) = guard.child.take() {
                    log::info!("Killing sidecar process on window close");
                    let _ = child.kill();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn find_available_port(start: u16, attempts: u16) -> u16 {
    for port in start..start + attempts {
        if std::net::TcpListener::bind(("127.0.0.1", port)).is_ok() {
            return port;
        }
    }
    start
}
