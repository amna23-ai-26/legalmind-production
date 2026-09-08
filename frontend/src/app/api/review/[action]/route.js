import { NextResponse } from "next/server";

const BACKEND = process.env.LEGALMIND_BACKEND_URL || "http://127.0.0.1:8000";

export async function POST(request, { params }) {
  const body = await request.json();

  const response = await fetch(`${BACKEND}/api/review/${params.action}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body)
  });

  const text = await response.text();

  return new NextResponse(text, {
    status: response.status,
    headers: {
      "Content-Type": "application/json"
    }
  });
}
