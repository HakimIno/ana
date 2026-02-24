import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import StyledJsxRegistry from "./registry";
import Providers from "./providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "AI Business Analyst | Smart Financial Insights",
  description: "Upload financial data and get professional AI-driven business insights.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={inter.className}>
        <Providers>
          <StyledJsxRegistry>
            {children}
          </StyledJsxRegistry>
        </Providers>
      </body>
    </html>
  );
}
