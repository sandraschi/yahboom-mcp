import { useCallback, useEffect, useState } from "react";

const ZOOM_LEVELS = [0.5, 0.6, 0.7, 0.8, 1.0, 1.25, 1.5, 2.0, 3.0];
const DEFAULT_INDEX = ZOOM_LEVELS.indexOf(1.0);

export function useZoom() {
  const [zoomIndex, setZoomIndex] = useState(() => {
    try {
      const saved = localStorage.getItem("tauri-zoom");
      const idx = saved ? ZOOM_LEVELS.indexOf(Number.parseFloat(saved)) : -1;
      return idx >= 0 ? idx : DEFAULT_INDEX;
    } catch {
      return DEFAULT_INDEX;
    }
  });

  const applyZoom = useCallback(async (level: number) => {
    localStorage.setItem("tauri-zoom", String(level));
    try {
      const { getCurrentWindow } = await import("@tauri-apps/api/window");
      await getCurrentWindow().setZoom(level);
    } catch {
      // Dev browser fallback: CSS scale on root
      const root = document.documentElement;
      root.style.transform = `scale(${level})`;
      root.style.transformOrigin = "top left";
      root.style.width = `${100 / level}%`;
      root.style.height = `${100 / level}%`;
    }
  }, []);

  useEffect(() => {
    const handler = (e: WheelEvent) => {
      if (!e.ctrlKey) return;
      e.preventDefault();
      setZoomIndex((prev) => {
        const next =
          e.deltaY < 0 ? Math.min(prev + 1, ZOOM_LEVELS.length - 1) : Math.max(prev - 1, 0);
        if (next !== prev) applyZoom(ZOOM_LEVELS[next]);
        return next;
      });
    };
    window.addEventListener("wheel", handler, { passive: false });
    const keyHandler = (e: KeyboardEvent) => {
      // Ctrl+0 (or Cmd+0): reset zoom to 100%
      if ((e.ctrlKey || e.metaKey) && e.key === "0") {
        e.preventDefault();
        setZoomIndex(DEFAULT_INDEX);
        applyZoom(ZOOM_LEVELS[DEFAULT_INDEX]);
      }
    };
    window.addEventListener("keydown", keyHandler);
    const saved = localStorage.getItem("tauri-zoom");
    if (saved) applyZoom(Number.parseFloat(saved));
    return () => {
      window.removeEventListener("wheel", handler);
      window.removeEventListener("keydown", keyHandler);
    };
  }, [applyZoom]);
}
