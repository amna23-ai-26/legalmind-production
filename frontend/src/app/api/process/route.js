export async function POST(request) {
  const BACKEND = process.env.LEGALMIND_BACKEND_URL || "http://127.0.0.1:8000";

  const body = await request.json();

  const response = await fetch(`${BACKEND}/api/process`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  const text = await response.text();

  return new Response(text, {
    status: response.status,
    headers: {
      "Content-Type": "application/json",
    },
  });
}
