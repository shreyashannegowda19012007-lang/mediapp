"use client";

import React, { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Sun, Moon, Monitor } from "lucide-react";
import { clsx } from "clsx";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="flex items-center rounded-lg border border-slate-200 dark:border-slate-800 p-0.5 bg-slate-100/50 dark:bg-slate-900/50 w-[108px] h-8" />
    );
  }

  const modes: Array<{ id: "light" | "dark" | "system"; label: string; icon: React.ReactNode }> = [
    { id: "light", label: "Light", icon: <Sun className="h-3.5 w-3.5" /> },
    { id: "dark", label: "Dark", icon: <Moon className="h-3.5 w-3.5" /> },
    { id: "system", label: "System", icon: <Monitor className="h-3.5 w-3.5" /> },
  ];

  return (
    <div
      role="group"
      aria-label="Theme selection"
      className="inline-flex items-center rounded-lg border border-slate-200 dark:border-slate-800 p-0.5 bg-slate-100/70 dark:bg-slate-900/70 shadow-xs"
    >
      {modes.map((mode) => {
        const isActive = theme === mode.id;
        return (
          <button
            key={mode.id}
            type="button"
            onClick={() => setTheme(mode.id)}
            title={`Switch to ${mode.label} mode`}
            className={clsx(
              "flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md transition-all duration-150 cursor-pointer",
              isActive
                ? "bg-white dark:bg-slate-800 text-sky-600 dark:text-sky-400 shadow-xs font-semibold"
                : "text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
            )}
          >
            {mode.icon}
            <span className="hidden sm:inline">{mode.label}</span>
          </button>
        );
      })}
    </div>
  );
}
