"use client";

import { motion } from "framer-motion";
import type { ChatMessage } from "@/lib/types";
import { agentMeta } from "./agentMeta";
import { cn } from "@/lib/utils";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const meta = agentMeta(message.agent);

  if (isUser) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        className="flex justify-end"
      >
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-accent px-4 py-2.5 text-[14px] leading-relaxed text-accent-fg shadow-soft">
          {message.text}
        </div>
      </motion.div>
    );
  }

  const Icon = meta.Icon;
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="flex flex-col gap-1.5"
    >
      <div className="flex items-center gap-1.5">
        <span className={cn("grid h-5 w-5 place-items-center rounded-md", meta.bg)}>
          <Icon className={cn("h-3 w-3", meta.text)} />
        </span>
        <span className={cn("text-[11px] font-medium", meta.text)}>{meta.label}</span>
      </div>
      <div className="max-w-[92%] rounded-2xl rounded-tl-md border border-border bg-surface px-4 py-2.5 text-[14px] leading-relaxed text-fg shadow-soft">
        <span className="whitespace-pre-wrap">{message.text}</span>
        {message.streaming && (
          <span className="ml-0.5 inline-block h-4 w-[2px] translate-y-0.5 animate-pulse bg-accent align-middle" />
        )}
      </div>
    </motion.div>
  );
}
