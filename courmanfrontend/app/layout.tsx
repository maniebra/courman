import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { ThemeProvider } from "next-themes";

import { Toaster } from "@/components/ui/sonner";

const inter = localFont({
  src: "./fonts/Inter.ttf",
  variable: "--font-inter",
  display: "swap",
});

const lexend = localFont({
  src: "./fonts/Lexend.ttf",
  variable: "--font-lexend",
  display: "swap",
});

// Persian glyph coverage; sits after Inter in the sans stack.
const vazirmatn = localFont({
  src: "./fonts/Vazirmatn.ttf",
  variable: "--font-vazirmatn",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Courman",
  description: "Course management admin",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${inter.variable} ${lexend.variable} ${vazirmatn.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          {children}
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  );
}
