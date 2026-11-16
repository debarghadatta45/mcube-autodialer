import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import clientPromise from "@/lib/mongodb";
import { verifyAdminToken } from "@/lib/adminAuth";

export async function GET(req: Request) {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("admin_token")?.value;

    if (!token || !verifyAdminToken(token)) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const client = await clientPromise;
    const db = client.db("vedantu_autodialer");

    // Fetch registered users
    const users = await db
      .collection("users")
      .find({})
      .sort({ registeredAt: -1 })
      .toArray();

    // Fetch bug reports
    const bugReports = await db
      .collection("bug_reports")
      .find({})
      .sort({ submittedAt: -1 })
      .toArray();

    // Calculate stats
    const totalUsers = users.length;
    const totalDownloads = users.reduce((acc, u) => acc + (u.downloads || 0), 0);
    const totalBugs = bugReports.length;
    const openBugs = bugReports.filter((b) => b.status === "Open" || !b.status).length;

    return NextResponse.json({
      success: true,
      stats: {
        totalUsers,
        totalDownloads,
        totalBugs,
        openBugs,
      },
      users: users.map((u) => ({
        id: u._id.toString(),
        name: u.name,
        email: u.email,
        department: u.department || "Sales",
        registeredAt: u.registeredAt,
        downloads: u.downloads || 0,
      })),
      bugReports: bugReports.map((b) => ({
        id: b._id.toString(),
        name: b.name,
        email: b.email,
        phone: b.phone || "",
        bugCategory: b.bugCategory || "General",
        message: b.message,
        submittedAt: b.submittedAt,
        status: b.status || "Open",
      })),
    });
  } catch (error: any) {
    console.error("Admin data fetch error:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
