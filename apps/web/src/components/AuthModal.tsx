"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Compass, Loader2, X } from "lucide-react";
import { authLogin, authRegister } from "@/lib/api";
import { setAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

export function AuthModal({ open, onClose, onSuccess }: { open: boolean; onClose: () => void; onSuccess: () => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setError(null);
    setBusy(true);
    try {
      const res = mode === "login" ? await authLogin(email, password) : await authRegister(email, password, name);
      setAuth(res.access_token, res.user);
      onSuccess();
      onClose();
    } catch (e: any) {
      setError(e?.message || "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div className="fixed inset-0 z-[70] grid place-items-center p-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
          <motion.div
            initial={{ opacity: 0, y: 16, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.97 }}
            transition={{ type: "spring", stiffness: 320, damping: 28 }}
            className="relative w-full max-w-sm overflow-hidden rounded-2xl border border-border bg-elevated shadow-lift"
          >
            <button onClick={onClose} className="absolute right-3 top-3 grid h-8 w-8 place-items-center rounded-lg text-faint transition hover:bg-surface-2 hover:text-fg">
              <X className="h-4 w-4" />
            </button>
            <div className="flex flex-col items-center gap-2 px-6 pt-8">
              <div className="grid h-11 w-11 place-items-center rounded-2xl bg-accent text-accent-fg shadow-glow">
                <Compass className="h-6 w-6" />
              </div>
              <h2 className="text-[17px] font-semibold tracking-tight">
                {mode === "login" ? "Welcome back" : "Create your account"}
              </h2>
              <p className="text-center text-[12.5px] text-muted">
                {mode === "login" ? "Sign in to sync your trips and preferences." : "Save trips and let the agents remember how you travel."}
              </p>
            </div>

            <div className="space-y-2.5 px-6 py-5">
              {mode === "register" && (
                <Field label="Name" value={name} onChange={setName} placeholder="Ada Lovelace" />
              )}
              <Field label="Email" type="email" value={email} onChange={setEmail} placeholder="you@example.com" onEnter={submit} />
              <Field label="Password" type="password" value={password} onChange={setPassword} placeholder="At least 8 characters" onEnter={submit} />
              {error && <div className="rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-[12px] text-danger">{error}</div>}
              <button
                onClick={submit}
                disabled={busy || !email || password.length < 8}
                className="mt-1 flex w-full items-center justify-center gap-2 rounded-xl bg-accent py-2.5 text-[13.5px] font-semibold text-accent-fg transition hover:opacity-90 disabled:opacity-50"
              >
                {busy && <Loader2 className="h-4 w-4 animate-spin" />}
                {mode === "login" ? "Sign in" : "Create account"}
              </button>
            </div>

            <div className="border-t border-border px-6 py-3 text-center text-[12px] text-muted">
              {mode === "login" ? "New to Odyssey? " : "Already have an account? "}
              <button
                onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(null); }}
                className="font-medium text-accent hover:underline"
              >
                {mode === "login" ? "Create an account" : "Sign in"}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
  onEnter,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  onEnter?: () => void;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-[11px] font-medium text-muted">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && onEnter?.()}
        placeholder={placeholder}
        className={cn("w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-[13.5px] text-fg outline-none placeholder:text-faint focus:border-accent/50")}
      />
    </label>
  );
}
