"use client";

import { DragEvent, UIEvent, useMemo, useRef, useState } from "react";
import { ExampleManifest } from "../lib/api";
import { PlayIcon, UploadIcon } from "./icons";

type Props = {
  name: string;
  value: string;
  examples: ExampleManifest[];
  loading: boolean;
  strict: boolean;
  onNameChange: (value: string) => void;
  onChange: (value: string) => void;
  onLoadExample: (example: ExampleManifest) => void;
  onStrictChange: (value: boolean) => void;
  onRun: () => void;
};

const intentLabel: Record<ExampleManifest["intent"], string> = {
  risky: "Risky",
  hardened: "Hardened",
  reference: "Reference"
};

export function ManifestEditor({
  name,
  value,
  examples,
  loading,
  strict,
  onNameChange,
  onChange,
  onLoadExample,
  onStrictChange,
  onRun
}: Props) {
  const [dragging, setDragging] = useState(false);
  const gutterRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const lineCount = useMemo(() => Math.max(value.split("\n").length, 1), [value]);

  function syncScroll(event: UIEvent<HTMLTextAreaElement>) {
    if (gutterRef.current) {
      gutterRef.current.scrollTop = event.currentTarget.scrollTop;
    }
  }

  async function readFile(file: File) {
    const text = await file.text();
    onChange(text);
    onNameChange(file.name);
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file) {
      void readFile(file);
    }
  }

  return (
    <div className="editor">
      <div className="editor-toolbar">
        <input
          className="manifest-name"
          value={name}
          onChange={(event) => onNameChange(event.target.value)}
          spellCheck={false}
          aria-label="Manifest name"
        />
        <div className="editor-actions">
          <label className="switch">
            <input type="checkbox" checked={strict} onChange={(event) => onStrictChange(event.target.checked)} />
            <span>Strict</span>
          </label>
          <button className="ghost-button" onClick={() => fileRef.current?.click()}>
            <UploadIcon className="icon-sm" />
            Upload
          </button>
          <button className="primary-button" onClick={onRun} disabled={loading}>
            <PlayIcon className="icon-sm" />
            {loading ? "Analyzing…" : "Run review"}
          </button>
          <input
            ref={fileRef}
            type="file"
            accept=".yaml,.yml,.txt"
            hidden
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) void readFile(file);
              event.target.value = "";
            }}
          />
        </div>
      </div>

      <div
        className={`editor-surface ${dragging ? "is-dragging" : ""}`}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <div className="editor-gutter" ref={gutterRef} aria-hidden="true">
          {Array.from({ length: lineCount }, (_, index) => (
            <span key={index}>{index + 1}</span>
          ))}
        </div>
        <textarea
          className="editor-input"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onScroll={syncScroll}
          spellCheck={false}
          placeholder="Paste or drop Kubernetes YAML here…"
        />
        {dragging && <div className="drop-overlay">Drop manifest to load</div>}
      </div>

      <div className="sample-row">
        <span className="sample-label">Samples</span>
        <div className="sample-chips">
          {examples.map((example) => (
            <button key={example.name} className={`sample-chip intent-${example.intent}`} onClick={() => onLoadExample(example)} title={example.description}>
              <span className="sample-intent">{intentLabel[example.intent]}</span>
              {example.title}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
