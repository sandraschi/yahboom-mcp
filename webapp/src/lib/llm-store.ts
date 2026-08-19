import { create } from "zustand";

const PROVIDER_KEY = "llm_provider";
const MODEL_KEY = "llm_model";

function readStorage(key: string, fallback: string): string {
  try {
    return localStorage.getItem(key) ?? fallback;
  } catch {
    return fallback;
  }
}

export interface GpuStatus {
  detected: boolean;
  gpu_name?: string | null;
  vram_total_gb?: number | null;
  vram_used_gb?: number | null;
  temp_c?: number | null;
  utilization_pct?: number | null;
}

interface LlmState {
  provider: string;
  model: string;
  ollamaConnected: boolean | null;
  lmstudioConnected: boolean | null;
  gpu: GpuStatus | null;
  setProvider: (provider: string) => void;
  setModel: (model: string) => void;
  setOllamaConnected: (v: boolean | null) => void;
  setLmstudioConnected: (v: boolean | null) => void;
  setGpu: (gpu: GpuStatus | null) => void;
}

export const useLlmStore = create<LlmState>((set) => ({
  provider: readStorage(PROVIDER_KEY, "ollama"),
  model: readStorage(MODEL_KEY, ""),
  ollamaConnected: null,
  lmstudioConnected: null,
  gpu: null,
  setProvider: (provider) =>
    set(() => {
      try {
        localStorage.setItem(PROVIDER_KEY, provider);
      } catch {
        /* storage unavailable */
      }
      return { provider };
    }),
  setModel: (model) =>
    set(() => {
      try {
        localStorage.setItem(MODEL_KEY, model);
      } catch {
        /* storage unavailable */
      }
      return { model };
    }),
  setOllamaConnected: (v) => set({ ollamaConnected: v }),
  setLmstudioConnected: (v) => set({ lmstudioConnected: v }),
  setGpu: (gpu) => set({ gpu }),
}));
