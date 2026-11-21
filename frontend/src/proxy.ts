import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const DEFAULT_API_INTERNAL_URL = "http://backend:8000";

export function proxy(request: NextRequest) {
  const configured = process.env.API_INTERNAL_URL?.trim();
  const backendOrigin = (
    configured && configured.length > 0 ? configured : DEFAULT_API_INTERNAL_URL
  ).replace(/\/+$/, "");

  const targetUrl = new URL(
    `${request.nextUrl.pathname}${request.nextUrl.search}`,
    backendOrigin,
  );

  return NextResponse.rewrite(targetUrl);
}

export const config = {
  matcher: ["/api/:path*", "/admin/:path*", "/static/:path*"],
};
