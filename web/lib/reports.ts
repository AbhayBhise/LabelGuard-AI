const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";

export async function downloadReport(scanId: string, format: "pdf" | "docx") {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("access_token")
      : null;
  const res = await fetch(`${API_BASE}/reports/${scanId}/${format}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error("Report fetch failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `report-${scanId}.${format}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
