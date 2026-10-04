import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { LoginForm } from "@/components/auth/AuthForms";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { getCurrentUser } from "@/lib/auth";
import { safeNextPath } from "@/lib/redirect";

export const metadata: Metadata = { title: "Log in — Skillaro" };

export default async function LoginPage({ searchParams }: PageProps<"/login">) {
  const next = safeNextPath((await searchParams).next);
  if (await getCurrentUser()) redirect(next);

  return (
    <AuthLayout
      title="Welcome back"
      subtitle={next === "/" ? "Log in to continue building your career readiness." : "Log in to continue to that page."}
      footer={
        <>
          New to Skillaro?{" "}
          <Link
            href={next === "/" ? "/register" : `/register?next=${encodeURIComponent(next)}`}
            className="font-semibold text-brand-blue underline underline-offset-4"
          >
            Create an account
          </Link>
        </>
      }
    >
      <LoginForm next={next} />
    </AuthLayout>
  );
}
