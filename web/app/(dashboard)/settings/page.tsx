export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Settings</h1>
        <p className="text-sm text-slate-500">
          Profile, organization, rules and notifications
        </p>
      </div>
      <div className="grid max-w-lg grid-cols-1 gap-4 rounded-xl border border-slate-200 bg-white p-5">
        {["Profile", "Organization", "Rules", "Notifications", "API Keys"].map(
          (t) => (
            <div
              key={t}
              className="flex items-center justify-between rounded-md border border-slate-100 px-4 py-3 text-sm"
            >
              <span className="font-medium text-slate-700">{t}</span>
              <span className="text-slate-300">›</span>
            </div>
          )
        )}
      </div>
    </div>
  );
}
