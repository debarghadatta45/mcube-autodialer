import { NextResponse } from "next/server";
import crypto from "crypto";

const SECRET = process.env.ADMIN_SESSION_SECRET || "vedantu_admin_secret_super_key_2026_x89";

export function generateAdminToken(email: string): string {
  const payload = `${email}:${Date.now()}`;
  const sig = crypto.createHmac("sha256", SECRET).update(payload).digest("hex");
  return Buffer.from(`${payload}:${sig}`).toString("base64");
}

export function verifyAdminToken(token: string): boolean {
  try {
    const decoded = Buffer.from(token, "base64").toString("utf-8");
    const parts = decoded.split(":");
    if (parts.length !== 3) return false;
    const [email, timestamp, sig] = parts;

    // Check expiration (24 hours)
    const age = Date.now() - parseInt(timestamp, 10);
    if (age > 24 * 60 * 60 * 1000) return false;

    const expectedSig = crypto.createHmac("sha256", SECRET).update(`${email}:${timestamp}`).digest("hex");
    return sig === expectedSig;
  } catch {
    return false;
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { email, password } = body;

    const targetEmail = (process.env.ADMIN_EMAIL || "debargha.datta@vedantu.com").toLowerCase().trim();
    const targetPassword = process.env.ADMIN_PASSWORD || "Mon#0812";

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
