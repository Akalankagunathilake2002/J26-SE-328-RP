import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { RegisterForm } from "@/components/auth/AuthForms";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { getCurrentUser } from "@/lib/auth";
import { loginPath, safeNextPath } from "@/lib/redirect";

export const metadata: Metadata = { title: "Create an account — Skillaro" };

export default async function RegisterPage({ searchParams }: PageProps<"/register">) {
  const next = safeNextPath((await searchParams).next);
  if (await getCurrentUser()) redirect(next);

  return (
    <AuthLayout
      title="Join Skillaro"
      subtitle="Create an account to see how your skills match what industry needs."
      footer={
        <>
          Already have an account?{" "}
          <Link href={loginPath(next)} className="font-semibold text-brand-blue underline underline-offset-4">
            Log in
          </Link>
        </>
      }
    >
      <RegisterForm next={next} />
    </AuthLayout>
  );
}
