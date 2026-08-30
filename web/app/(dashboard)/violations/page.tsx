export default function ViolationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Violations</h1>
        <p className="text-sm text-slate-500">
          All compliance violations detected across scans
        </p>
      </div>
      <div className="rounded-xl border border-slate-200 bg-white p-12 text-center text-sm text-slate-400">
        Violations list requires the backend — connect to populate this view.
      </div>
    </div>
  );
}
