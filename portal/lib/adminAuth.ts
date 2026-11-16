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
