import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { LocaleProvider } from "@/components/locale-context";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Velie CI — AI Code Review Dashboard",
  description: "AI-powered code review for every PR | すべてのPRにAIコードレビュー",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased bg-gray-950 text-gray-100`}>
        <LocaleProvider>
          {children}
        </LocaleProvider>
      </body>
    </html>
  );
}
