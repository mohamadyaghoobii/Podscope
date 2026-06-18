"use client";

import { useState } from "react";
import { CheckIcon, CopyIcon } from "./icons";

export function CopyButton({ text, label = "Copy" }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <button type="button" className="copy-button" onClick={copy} aria-label={label}>
      {copied ? <CheckIcon className="icon-xs" /> : <CopyIcon className="icon-xs" />}
      <span>{copied ? "Copied" : label}</span>
    </button>
  );
}
