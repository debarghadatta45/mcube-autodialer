import { NextResponse } from "next/server";
import clientPromise from "@/lib/mongodb";
import path from "path";
import fs from "fs";

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const email = searchParams.get("email")?.toLowerCase().trim();
    const os = searchParams.get("os")?.toLowerCase().trim();

    if (!email || !email.endsWith("@vedantu.com")) {
      return new NextResponse("Access Denied: Only @vedantu.com registered users can download.", {
        status: 403,
      });
    }

    const client = await clientPromise;
    const db = client.db("vedantu_autodialer");
    const usersCollection = db.collection("users");

    // Verify user is registered in MongoDB
    const user = await usersCollection.findOne({ email });
    if (!user) {
      return new NextResponse("Access Denied: Please register your @vedantu.com email first.", {
        status: 403,
      });
    }

    // Increment download counter
    await usersCollection.updateOne(
      { email },
      {
        $inc: { downloads: 1 },
        $set: { lastDownloadAt: new Date(), lastDownloadedOS: os || "windows" }
      }
    );

    let filename = "MCUBE_AutoDialer.exe";
    if (os === "mac" || os === "macos" || os === "dmg") {
      filename = "MCUBE_AutoDialer.dmg";
    }

    const filePath = path.join(process.cwd(), "public", "downloads", filename);

    if (!fs.existsSync(filePath)) {
      return new NextResponse(`File ${filename} not found on server.`, { status: 404 });
    }

    const fileBuffer = fs.readFileSync(filePath);

    let contentType = "application/vnd.microsoft.portable-executable";
    if (filename.endsWith(".dmg")) {
      contentType = "application/x-apple-diskimage";
    }

    return new NextResponse(fileBuffer, {
      status: 200,
      headers: {
        "Content-Disposition": `attachment; filename="${filename}"`,
        "Content-Type": contentType,
        "Content-Length": fileBuffer.length.toString(),
      },
    });
  } catch (err: any) {
    console.error("Download route error:", err);
    return new NextResponse("Internal Server Error", { status: 500 });
  }
}
