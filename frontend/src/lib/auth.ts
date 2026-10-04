import "server-only";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { cache } from "react";

import { loginPath } from "@/lib/redirect";

// Backend requests go through the API gateway to the auth-service microservice. Only the Next.js
// server makes them; the browser never sees the token.
const API_GATEWAY_URL = process.env.API_GATEWAY_URL ?? "http://localhost:8080";
export const SESSION_COOKIE = "session";

export type User = {
  id: string;
  full_name: string;
  email: string;
  created_at: string;
};

export class AuthServiceError extends Error {}

async function callAuthService(path: string, init: RequestInit = {}): Promise<Response> {
  try {
    return await fetch(`${API_GATEWAY_URL}${path}`, {
      ...init,
      cache: "no-store",
      headers: { "Content-Type": "application/json", ...init.headers },
    });
  } catch {
    throw new AuthServiceError(UNAVAILABLE);
  }
}

const UNAVAILABLE = "We can't reach the sign-in service right now. Please try again shortly.";

async function errorFrom(response: Response): Promise<AuthServiceError> {
  if (response.status >= 502) return new AuthServiceError(UNAVAILABLE);
  const body = await response.json().catch(() => null);
  const detail = body?.detail;
  if (typeof detail === "string") return new AuthServiceError(detail);
  if (Array.isArray(detail) && typeof detail[0]?.msg === "string") return new AuthServiceError(detail[0].msg);
  return new AuthServiceError("Something went wrong. Please try again.");
}

export async function registerAccount(fullName: string, email: string, password: string): Promise<void> {
  const response = await callAuthService("/auth/register", {
    method: "POST",
    body: JSON.stringify({ full_name: fullName, email, password }),
  });
  if (!response.ok) throw await errorFrom(response);
}

/** Logs in and stores the access token in an httpOnly session cookie. */
export async function startSession(email: string, password: string): Promise<void> {
  const response = await callAuthService("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) throw await errorFrom(response);

  const { access_token, expires_in } = (await response.json()) as { access_token: string; expires_in: number };
  (await cookies()).set(SESSION_COOKIE, access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: expires_in,
  });
}

export async function endSession(): Promise<void> {
  (await cookies()).delete(SESSION_COOKIE);
}

/** The logged-in user, or null when there is no valid session (or the auth service is down). */
export const getCurrentUser = cache(async (): Promise<User | null> => {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token) return null;
  try {
    const response = await callAuthService("/auth/me", { headers: { Authorization: `Bearer ${token}` } });
    return response.ok ? ((await response.json()) as User) : null;
  } catch {
    return null;
  }
});

/** The logged-in user; anyone else is sent to the login page and brought back to `currentPath`. */
export async function requireUser(currentPath: string): Promise<User> {
  const user = await getCurrentUser();
  if (!user) redirect(loginPath(currentPath));
  return user;
}
