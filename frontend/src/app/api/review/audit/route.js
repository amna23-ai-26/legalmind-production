import { NextResponse } from "next/server";

const BACKEND = process.env.LEGALMIND_BACKEND_URL || "http://127.0.0.1:8000";

export async function GET() {
  const response = await fetch(`${BACKEND}/api/review/audit`, {
    cache: "no-store"
  });

  const text = await response.text();

  return new NextResponse(text, {
    status: response.status,
    headers: {
      "Content-Type": "application/json"
    }
  });
}
