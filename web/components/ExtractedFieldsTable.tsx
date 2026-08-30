"use client";

type Field = {
  field: string;
  value: string | null;
  confidence?: number | null;
  extraction_method?: string;
};

export default function ExtractedFieldsTable({ fields }: { fields: Field[] }) {
  if (!fields || fields.length === 0) {
    return <p className="py-6 text-sm text-slate-400">No fields extracted.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-400">
            <th className="px-4 py-2">Field</th>
            <th className="px-4 py-2">Extracted Value</th>
            <th className="px-4 py-2">Method</th>
          </tr>
        </thead>
        <tbody>
          {fields.map((f) => (
            <tr key={f.field} className="border-b border-slate-50">
              <td className="px-4 py-2 font-medium text-slate-700">
                {f.field.replace(/_/g, " ")}
              </td>
              <td
                className={`px-4 py-2 font-mono text-xs ${
                  f.value
                    ? "text-slate-800"
                    : "italic text-danger"
                }`}
              >
                {f.value || "(not found)"}
              </td>
              <td className="px-4 py-2 text-xs text-slate-400">
                {f.extraction_method || "ocr"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
