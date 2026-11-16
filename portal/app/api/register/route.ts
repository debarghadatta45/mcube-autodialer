import { NextResponse } from "next/server";
import clientPromise from "@/lib/mongodb";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { name, email, phone, role, os } = body;

    // Strict validation
    if (!email || typeof email !== "string") {
      return NextResponse.json(
        { error: "Email address is required." },
        { status: 400 }
      );
    }

    const cleanEmail = email.trim().toLowerCase();

    // Verify @vedantu.com domain or admin email
    const isAuthorized = cleanEmail.endsWith("@vedantu.com") || cleanEmail === "dadeb349@gmail.com";
    if (!isAuthorized) {
      return NextResponse.json(
        {
          error: "Access Denied: Only official @vedantu.com email addresses are authorized to register."
        },
        { status: 403 }
      );
    }

    const client = await clientPromise;
    const db = client.db("vedantu_autodialer");
    const usersCollection = db.collection("users");

    // Check if user already registered
    const existingUser = await usersCollection.findOne({ email: cleanEmail });

    const now = new Date();

    if (existingUser) {
      await usersCollection.updateOne(
        { email: cleanEmail },
        {
          $set: {
            lastLoginAt: now,
            ...(phone ? { phone } : {}),
            ...(role ? { role } : {}),
            ...(os ? { os } : {})
          },
          $inc: { loginCount: 1 }
        }
      );

      return NextResponse.json({
        success: true,
        message: `Welcome back, ${existingUser.name || "Vedantite"}! Your access is active.`,
        isExisting: true,
        user: {
          name: existingUser.name,
          email: cleanEmail,
          registeredAt: existingUser.registeredAt
        }
      });
    }

    // New Registration
    const newUser = {
      name: name?.trim() || cleanEmail.split("@")[0],
      email: cleanEmail,
      phone: phone?.trim() || "",
      role: role?.trim() || "Sales",
      os: os || "Windows",
      registeredAt: now,
      lastLoginAt: now,
      loginCount: 1,
      downloads: 0
    };

    await usersCollection.insertOne(newUser);

    return NextResponse.json({
      success: true,
      message: `Registration successful! Welcome to the Vedantu Auto-Dialer Portal, ${newUser.name}.`,
      isExisting: false,
      user: {
        name: newUser.name,
        email: cleanEmail,
        registeredAt: newUser.registeredAt
      }
    });
  } catch (error: any) {
    console.error("Registration API error:", error);
    return NextResponse.json(
      { error: "Internal Server Error: Unable to complete registration at this time." },
      { status: 500 }
    );
  }
}
