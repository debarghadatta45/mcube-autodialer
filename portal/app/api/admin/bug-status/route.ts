import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { ObjectId } from "mongodb";
import clientPromise from "@/lib/mongodb";
import { verifyAdminToken } from "../login/route";

export async function PATCH(req: Request) {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("admin_token")?.value;

    if (!token || !verifyAdminToken(token)) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id, status } = await req.json();
    if (!id || !status) {
      return NextResponse.json({ error: "Missing id or status" }, { status: 400 });
    }

    const client = await clientPromise;
    const db = client.db("vedantu_autodialer");

    await db.collection("bug_reports").updateOne(
      { _id: new ObjectId(id) },
      { $set: { status, updatedAt: new Date() } }
    );

    return NextResponse.json({ success: true, message: `Bug marked as ${status}` });
  } catch (error: any) {
    console.error("Update bug status error:", error);
    return NextResponse.json({ error: "Failed to update bug status" }, { status: 500 });
  }
}
