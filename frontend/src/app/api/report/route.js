import { NextResponse } from "next/server";
import { readFile } from "fs/promises";

export async function GET() {
  const filePath = "/content/drive/MyDrive/legalmind/outputs/reports/application_runtime.docx";

  try {
    const file = await readFile(filePath);

    return new NextResponse(file, {
      status: 200,
      headers: {
        "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "Content-Disposition": 'attachment; filename="LegalMind_Application_Runtime_Report.docx"',
      },
    });
  } catch (error) {
    return NextResponse.json(
      {
        status: "ERROR",
        message: "Report file is not available.",
      },
      { status: 404 }
    );
  }
}
