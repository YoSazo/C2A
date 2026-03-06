#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::fs::{self, OpenOptions};
use std::io::Write;
use std::net::TcpStream;
#[cfg(windows)]
use std::os::windows::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread;
use std::time::{Duration, Instant};
use tauri::api::dialog::blocking::MessageDialogBuilder;
use tauri::{Manager, State, WindowBuilder, WindowUrl};

const BACKEND_PORT: u16 = 8765;
const BACKEND_HOST: &str = "127.0.0.1";
#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x08000000;

struct BackendProcess {
    child: Mutex<Option<Child>>,
}

fn startup_log_path() -> PathBuf {
    std::env::temp_dir().join("c2a_training_startup.log")
}

fn backend_log_path() -> PathBuf {
    std::env::temp_dir().join("c2a_training_backend.log")
}

fn log_line(message: &str) {
    let path = startup_log_path();
    if let Some(parent) = path.parent() {
        let _ = fs::create_dir_all(parent);
    }
    if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(path) {
        let _ = writeln!(file, "{}", message);
    }
}

fn push_candidate(candidates: &mut Vec<PathBuf>, path: PathBuf) {
    candidates.push(path);
}

fn normalize(path: &Path) -> PathBuf {
    path.canonicalize().unwrap_or_else(|_| path.to_path_buf())
}

fn resolve_backend_script(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    let mut candidates: Vec<PathBuf> = Vec::new();

    if let Some(path) = app.path_resolver().resolve_resource("c2a_runtime/C2A.py") {
        push_candidate(&mut candidates, path);
    }
    if let Some(path) = app.path_resolver().resolve_resource("C2A.py") {
        push_candidate(&mut candidates, path);
    }

    if let Some(dir) = app.path_resolver().resource_dir() {
        push_candidate(&mut candidates, dir.join("c2a_runtime").join("C2A.py"));
        push_candidate(&mut candidates, dir.join("resources").join("c2a_runtime").join("C2A.py"));
        push_candidate(&mut candidates, dir.join("_up_").join("c2a_runtime").join("C2A.py"));
        push_candidate(&mut candidates, dir.join("C2A.py"));
        push_candidate(&mut candidates, dir.join("resources").join("C2A.py"));
        push_candidate(&mut candidates, dir.join("_up_").join("C2A.py"));
    }

    if let Ok(cwd) = std::env::current_dir() {
        push_candidate(&mut candidates, cwd.join("c2a_runtime").join("C2A.py"));
        push_candidate(&mut candidates, cwd.join("_up_").join("c2a_runtime").join("C2A.py"));
        push_candidate(&mut candidates, cwd.join("C2A.py"));
        push_candidate(&mut candidates, cwd.join("_up_").join("C2A.py"));
        push_candidate(
            &mut candidates,
            cwd.join("..").join("..").join("..").join("c2a_runtime").join("C2A.py"),
        );
        push_candidate(&mut candidates, cwd.join("..").join("..").join("..").join("C2A.py"));
    }

    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            push_candidate(&mut candidates, dir.join("c2a_runtime").join("C2A.py"));
            push_candidate(&mut candidates, dir.join("_up_").join("c2a_runtime").join("C2A.py"));
            push_candidate(&mut candidates, dir.join("C2A.py"));
            push_candidate(&mut candidates, dir.join("_up_").join("C2A.py"));
            push_candidate(
                &mut candidates,
                dir.join("..").join("..").join("..").join("c2a_runtime").join("C2A.py"),
            );
            push_candidate(&mut candidates, dir.join("..").join("..").join("..").join("C2A.py"));
            push_candidate(
                &mut candidates,
                dir.join("..").join("Resources").join("c2a_runtime").join("C2A.py"),
            );
            push_candidate(
                &mut candidates,
                dir.join("..").join("Resources").join("_up_").join("c2a_runtime").join("C2A.py"),
            );
            push_candidate(
                &mut candidates,
                dir.join("..").join("Resources").join("C2A.py"),
            );
            push_candidate(
                &mut candidates,
                dir.join("..").join("Resources").join("_up_").join("C2A.py"),
            );
        }
    }

    let mut checked: Vec<String> = Vec::new();
    for candidate in candidates {
        let normalized = normalize(&candidate);
        checked.push(normalized.display().to_string());
        if normalized.exists() {
            return Ok(normalized);
        }
    }

    Err(format!("C2A.py not found. Checked: {}", checked.join(" | ")))
}

fn configure_backend_command(command: &mut Command, cwd: &Path, backend_log: &Path) {
    let stdout_file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(backend_log)
        .ok();
    let stderr_file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(backend_log)
        .ok();

    command
        .current_dir(cwd)
        .stdin(Stdio::null())
        .stdout(stdout_file.map(Stdio::from).unwrap_or(Stdio::null()))
        .stderr(stderr_file.map(Stdio::from).unwrap_or(Stdio::null()));

    #[cfg(windows)]
    {
        command.creation_flags(CREATE_NO_WINDOW);
    }
}

fn spawn_backend(app: &tauri::AppHandle) -> Result<Child, String> {
    let script_path = resolve_backend_script(app)?;
    let cwd = script_path
        .parent()
        .map(Path::to_path_buf)
        .unwrap_or_else(|| PathBuf::from("."));
    let backend_log = backend_log_path();

    log_line(&format!("Backend script: {}", script_path.display()));
    log_line(&format!("Backend cwd: {}", cwd.display()));
    log_line(&format!("Backend log: {}", backend_log.display()));

    let mut py_launcher = Command::new("py");
    py_launcher
        .arg("-3")
        .arg(&script_path)
        .arg("--no-browser")
        .arg("--port")
        .arg(BACKEND_PORT.to_string());
    configure_backend_command(&mut py_launcher, &cwd, &backend_log);

    match py_launcher.spawn() {
        Ok(child) => {
            log_line("Backend spawn: py -3 success");
            Ok(child)
        }
        Err(py_err) => {
            log_line(&format!("Backend spawn: py -3 failed: {}", py_err));
            let mut python = Command::new("python");
            python
                .arg(&script_path)
                .arg("--no-browser")
                .arg("--port")
                .arg(BACKEND_PORT.to_string());
            configure_backend_command(&mut python, &cwd, &backend_log);

            match python.spawn() {
                Ok(child) => {
                    log_line("Backend spawn: python success");
                    Ok(child)
                }
                Err(python_err) => {
                    log_line(&format!("Backend spawn: python failed: {}", python_err));
                    Err(format!(
                        "Could not launch Python backend. See log: {}",
                        backend_log.display()
                    ))
                }
            }
        }
    }
}

fn wait_for_backend(timeout: Duration) -> bool {
    let addr = format!("{}:{}", BACKEND_HOST, BACKEND_PORT);
    let start = Instant::now();

    while start.elapsed() < timeout {
        if TcpStream::connect(&addr).is_ok() {
            log_line("Backend health check: ready");
            return true;
        }
        thread::sleep(Duration::from_millis(150));
    }

    log_line("Backend health check: timed out");
    false
}

fn main() {
    log_line("Desktop startup begin");
    tauri::Builder::default()
        .manage(BackendProcess {
            child: Mutex::new(None),
        })
        .setup(|app| {
            let state: State<BackendProcess> = app.state();
            let child = match spawn_backend(&app.handle()) {
                Ok(child) => child,
                Err(err) => {
                    MessageDialogBuilder::new("C2A failed to start", &err)
                        .kind(tauri::api::dialog::MessageDialogKind::Error)
                        .show();
                    return Err(err.into());
                }
            };

            {
                let mut slot = state.child.lock().map_err(|_| "Could not lock backend process")?;
                *slot = Some(child);
            }

            if !wait_for_backend(Duration::from_secs(15)) {
                let msg = format!(
                    "C2A backend did not start in time.\nCheck: {}",
                    backend_log_path().display()
                );
                MessageDialogBuilder::new("C2A failed to start", &msg)
                    .kind(tauri::api::dialog::MessageDialogKind::Error)
                    .show();
                return Err(msg.into());
            }

            let url = format!("http://{}:{}/", BACKEND_HOST, BACKEND_PORT);
            WindowBuilder::new(app, "main", WindowUrl::External(url.parse().unwrap()))
                .title("C2A Training Grounds")
                .inner_size(1400.0, 900.0)
                .min_inner_size(1100.0, 700.0)
                .resizable(true)
                .center()
                .build()
                .map_err(|e| format!("Failed to create window: {e}"))?;

            log_line("Desktop window created");
            Ok(())
        })
        .on_window_event(|event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event.event() {
                let app = event.window().app_handle();
                let state: State<BackendProcess> = app.state();
                let mut slot = match state.child.lock() {
                    Ok(guard) => guard,
                    Err(_) => return,
                };
                if let Some(child) = slot.as_mut() {
                    let _ = child.kill();
                }
                *slot = None;
                log_line("Desktop shutdown complete");
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}