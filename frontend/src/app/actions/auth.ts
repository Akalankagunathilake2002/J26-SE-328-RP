"use server";

import { redirect } from "next/navigation";

import { AuthServiceError, endSession, registerAccount, startSession } from "@/lib/auth";
import { safeNextPath } from "@/lib/redirect";

type Field = "fullName" | "email" | "password" | "confirmPassword";

export type AuthFormState =
  | {
      errors?: Partial<Record<Field, string>>;
      message?: string;
      values?: { fullName?: string; email?: string };
    }
  | undefined;

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function read(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value : "";
}

function messageFor(error: unknown): string {
  return error instanceof AuthServiceError ? error.message : "Something went wrong. Please try again.";
}

export async function login(_state: AuthFormState, formData: FormData): Promise<AuthFormState> {
  const email = read(formData, "email").trim();
  const password = read(formData, "password");

  const errors: Partial<Record<Field, string>> = {};
  if (!EMAIL_PATTERN.test(email)) errors.email = "Enter a valid email address.";
  if (!password) errors.password = "Enter your password.";
  if (Object.keys(errors).length > 0) return { errors, values: { email } };

  try {
    await startSession(email, password);
  } catch (error) {
    return { message: messageFor(error), values: { email } };
  }
  redirect(safeNextPath(read(formData, "next")));
}

export async function register(_state: AuthFormState, formData: FormData): Promise<AuthFormState> {
  const fullName = read(formData, "fullName").trim();
  const email = read(formData, "email").trim();
  const password = read(formData, "password");
  const confirmPassword = read(formData, "confirmPassword");
  const values = { fullName, email };

  const errors: Partial<Record<Field, string>> = {};
  if (fullName.length < 2) errors.fullName = "Enter your full name.";
  if (!EMAIL_PATTERN.test(email)) errors.email = "Enter a valid email address.";
  if (password.length < 8) errors.password = "Use at least 8 characters.";
  if (confirmPassword !== password) errors.confirmPassword = "Passwords don't match.";
  if (Object.keys(errors).length > 0) return { errors, values };

  try {
    await registerAccount(fullName, email, password);
    await startSession(email, password);
  } catch (error) {
    return { message: messageFor(error), values };
  }
  redirect(safeNextPath(read(formData, "next")));
}

export async function logout(): Promise<void> {
  await endSession();
  redirect("/");
}
