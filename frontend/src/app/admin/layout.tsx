import { requireAdmin } from "@/lib/auth";
import { fetchSsksCandidateRelationships } from "@/lib/ssksApi";
import { AdminSidebar } from "@/components/admin/AdminSidebar";
import { AdminHeader } from "@/components/admin/AdminHeader";

export const metadata = {
  title: "Admin Portal — Skillaro SSKS Knowledge Management",
  description: "Administrative console for managing canonical skills, roles, and verified relationships in Skillaro.",
};

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Enforces authenticated session with role 'admin'
  const user = await requireAdmin("/admin");

  // Fetch candidate relationships to calculate pending badge count
  let pendingCount = 0;
  try {
    const candidates = await fetchSsksCandidateRelationships({ review_status: "PENDING", limit: 100 });
    pendingCount = candidates.length;
  } catch {
    pendingCount = 0;
  }

  return (
    <div className="flex min-h-screen flex-col bg-[#FAF8F5] text-ink md:h-screen md:flex-row md:overflow-hidden">
      <AdminSidebar pendingCount={pendingCount} />
      <div className="flex flex-1 flex-col min-w-0 md:h-screen">
        <AdminHeader user={user} />
        <main className="flex-1 overflow-y-auto p-4 sm:p-5 lg:p-6">
          <div className="mx-auto max-w-5xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
