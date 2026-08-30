import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import AuthGuard from "@/components/AuthGuard";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex flex-1 flex-col">
          <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-6">
            <div className="w-72 rounded-md border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm text-slate-400">
              Search products, barcodes…
            </div>
            <div className="flex items-center gap-4">
              <button className="text-slate-500 hover:text-slate-700">
                🔔
              </button>
              <Link
                href="/"
                className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-200 text-xs"
              >
                OS
              </Link>
            </div>
          </header>
          <main className="flex-1 overflow-y-auto bg-[#F8FAFC] p-6">
            {children}
          </main>
        </div>
      </div>
    </AuthGuard>
  );
}
