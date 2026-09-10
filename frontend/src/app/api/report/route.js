import { NextResponse } from "next/server";

const BACKEND = process.env.LEGALMIND_BACKEND_URL || "http://127.0.0.1:8000";

// Previously this read a hardcoded Google Colab path
// ("/content/drive/MyDrive/legalmind/outputs/reports/...") straight off
// the Next.js server's own filesystem instead of calling the backend -
// that path never exists on Vercel (or anywhere outside the original
// Colab notebook), so this route always fell into the catch block and
// returned "Report file is not available." regardless of whether a
// report had actually been generated. Every other /api/* route proxies
// to the FastAPI backend; this one now does the same, streaming the
// generated .docx through instead of reading local disk.
export async function GET() {
  const response = await fetch(`${BACKEND}/api/report`, {
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    return new NextResponse(text, {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("content-type") || "application/json",
      },
    });
  }

  const fileBuffer = await response.arrayBuffer();

  return new NextResponse(fileBuffer, {
    status: 200,
    headers: {
      "Content-Type":
        response.headers.get("content-type") ||
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "Content-Disposition":
        response.headers.get("content-disposition") ||
        'attachment; filename="LegalMind_Legal_Intelligence_Report.docx"',
    },
  });
}
