import { NextResponse } from "next/server";
import clientPromise from "@/lib/mongodb";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { name, email, phone, message, bugCategory } = body;

    if (!message || message.trim().length === 0) {
      return NextResponse.json({ error: "Message cannot be empty." }, { status: 400 });
    }

    const client = await clientPromise;
    const db = client.db("vedantu_autodialer");
    const reportsCollection = db.collection("bug_reports");

    await reportsCollection.insertOne({
      name: name || "Anonymous Vedantite",
      email: email || "unknown@vedantu.com",
      phone: phone || "",
      bugCategory: bugCategory || "General",
      message: message.trim(),
      submittedAt: new Date(),
      status: "Open"
    });

    return NextResponse.json({
      success: true,
      message: "Thank you! Your bug report has been forwarded to Debargha Datta."
    });
  } catch (error: any) {
    console.error("Bug report API error:", error);
    return NextResponse.json({ error: "Failed to submit report." }, { status: 500 });
  }
}
