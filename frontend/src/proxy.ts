import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/lib/auth";
import { loginPath } from "@/lib/redirect";

// Quick check before protected pages render: no session cookie means "go and log in".
// Each protected page also verifies the session with the auth service (see requireUser).
export function proxy(request: NextRequest) {
  if (request.cookies.has(SESSION_COOKIE)) return NextResponse.next();

  const next = request.nextUrl.pathname + request.nextUrl.search;
  return NextResponse.redirect(new URL(loginPath(next), request.url));
}

// Pages that need a logged-in user: every nav link except Home (components/home/links.ts).
export const config = {
  matcher: ["/skills-profile/:path*", "/market-pulse/:path*", "/skill-analysis/:path*"],
};
