import { invoke } from "@tauri-apps/api/core";

export async function getBackendPort(): Promise<number> {
  return invoke<number>("get_backend_port");
}

export async function greet(name: string): Promise<string> {
  return invoke<string>("greet", { name });
}
