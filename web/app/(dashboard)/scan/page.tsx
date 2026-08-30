"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";

const steps = [
  "Image preprocessing",
  "Label region detection",
  "Text extraction (OCR)",
  "Semantic field extraction (AI)",
  "Compliance rule checking",
  "Report generation",
];

export default function NewScanPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [productName, setProductName] = useState("");
  const [netWeight, setNetWeight] = useState("");
  const [category, setCategory] = useState("food");
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) setFile(f);
  }

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setProgress(5);
    const form = new FormData();
    form.append("images", file);
    if (productName) form.append("product_name", productName);
    if (netWeight) form.append("net_weight_grams", netWeight);
    form.append("category", category);
    form.append("source", "web");

    const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";
    const auth = `Bearer ${
      typeof window !== "undefined"
        ? localStorage.getItem("access_token") || ""
        : ""
    }`;

    try {
      const res = await fetch(`${base}/scans`, {
        method: "POST",
        body: form,
        headers: { Authorization: auth },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");

      // Poll the real pipeline status and only navigate once it finishes.
      const poll = async () => {
        try {
          const s = await fetch(`${base}/scans/${data.scan_id}/status`, {
            headers: { Authorization: auth },
          }).then((r) => r.json());
          setProgress(s.progress ?? 10);
          if (s.status === "complete") {
            router.push(`/scan/${data.scan_id}`);
            return;
          }
          if (s.status === "failed") {
            alert("Scan processing failed. Please try another image.");
            setUploading(false);
            return;
          }
        } catch {
          /* transient error — keep polling */
        }
        setTimeout(poll, 1200);
      };
      poll();
    } catch (err: any) {
      alert(err.message);
      setUploading(false);
    }
  }

  const currentStep = Math.min(
    steps.length - 1,
    Math.floor((progress / 100) * steps.length)
  );

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">New Scan</h1>
        <p className="text-sm text-slate-500">
          Upload a product label image for compliance checking
        </p>
      </div>

      {!uploading && (
        <div
          onDrop={onDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => inputRef.current?.click()}
          className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-white p-12 text-center transition hover:border-[#1B4FD8]"
        >
          <div className="text-4xl">📷</div>
          <p className="mt-3 font-medium text-slate-700">
            {file ? file.name : "Drag & drop a label image, or click to browse"}
          </p>
          <p className="mt-1 text-xs text-slate-400">
            JPEG, PNG, WebP · up to 10MB
          </p>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && setFile(e.target.files[0])}
          />
        </div>
      )}

      {file && !uploading && (
        <>
          <div className="grid grid-cols-2 gap-4 rounded-xl border border-slate-200 bg-white p-5">
            <div>
              <label className="text-xs font-medium text-slate-600">
                Product Name (optional)
              </label>
              <input
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                placeholder="e.g. Maggi 2-Minute Noodles"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600">
                Net Weight / Volume (g)
              </label>
              <input
                value={netWeight}
                onChange={(e) => setNetWeight(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                placeholder="e.g. 340"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600">
                Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              >
                <option value="food">Food</option>
                <option value="pharma">Pharma</option>
                <option value="cosmetics">Cosmetics</option>
                <option value="electronics">Electronics</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleUpload}
            className="w-full rounded-md bg-[#1B4FD8] py-3 font-semibold text-white hover:bg-[#1740ad]"
          >
            Run Compliance Check
          </button>
        </>
      )}

      {uploading && (
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="text-sm font-semibold text-slate-700">
            Processing your scan…
          </h2>
          <div className="mt-4 space-y-2.5">
            {steps.map((s, i) => (
              <div key={s} className="flex items-center gap-3 text-sm">
                <span
                  className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] ${
                    i < currentStep
                      ? "bg-success text-white"
                      : i === currentStep
                      ? "bg-[#1B4FD8] text-white"
                      : "bg-slate-100 text-slate-400"
                  }`}
                >
                  {i < currentStep ? "✓" : i + 1}
                </span>
                <span
                  className={
                    i <= currentStep ? "text-slate-800" : "text-slate-400"
                  }
                >
                  {s}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-200">
            <div
              className="h-full bg-[#1B4FD8] transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
