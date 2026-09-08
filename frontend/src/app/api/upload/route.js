export async function POST(request) {
  const BACKEND = process.env.LEGALMIND_BACKEND_URL || "http://127.0.0.1:8000";

  const formData = await request.formData();

  const response = await fetch(`${BACKEND}/api/upload`, {
    method: "POST",
    body: formData,
  });

  const text = await response.text();

  return new Response(text, {
    status: response.status,
    headers: {
      "Content-Type": "application/json",
    },
  });
}
