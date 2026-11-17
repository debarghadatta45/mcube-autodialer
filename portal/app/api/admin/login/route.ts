import { NextResponse } from "next/server";
import { generateAdminToken } from "@/lib/adminAuth";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { email, password } = body;

    const targetEmail = (process.env.ADMIN_EMAIL || "").toLowerCase().trim();
    const targetPassword = process.env.ADMIN_PASSWORD || "";

    const inputEmail = (email || "").toLowerCase().trim();
    const inputPassword = password || "";

    if (inputEmail !== targetEmail || inputPassword !== targetPassword) {
      return NextResponse.json({ error: "Invalid Admin email or password." }, { status: 401 });
    }

    const token = generateAdminToken(inputEmail);
    const response = NextResponse.json({
      success: true,
      email: inputEmail,
      message: "Admin authentication successful."
    });

    response.cookies.set("admin_token", token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 24, // 24 hours
      path: "/"
    });

    return response;
  } catch (error: any) {
    return NextResponse.json({ error: "Authentication failed." }, { status: 500 });
  }
}
