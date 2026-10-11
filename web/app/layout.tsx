import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EU AI Act — kmail.at",
  description:
    "Read the Act. Then apply it. Regulation (EU) 2024/1689 in full — searchable and structured, with the classification ladder, the procedures, the worked cases and an agent that shows its work.",
  applicationName: "kmail.at — EU AI Act",
  authors: [{ name: "Mohammed Kmail", url: "https://kmail.at" }],
  creator: "Mohammed Kmail",
  icons: {
    icon: [{ url: "/logo-mark.png", type: "image/png" }],
    apple: [{ url: "/logo-mark.png" }],
  },
  openGraph: {
    title: "EU AI Act — kmail.at",
    description:
      "Read the Act. Then apply it. The full EUR-Lex text, the procedures, the cases and the charts.",
    url: "https://kmail.at",
    siteName: "kmail.at",
    type: "website",
  },
};

/**
 * Set the theme before first paint so there is no flash. Mirrors kmail.at:
 * an explicit choice in localStorage wins, otherwise follow the OS.
 */
const themeScript = `(function(){try{var t=localStorage.getItem('kmail-theme');
var d=t?t==='dark':window.matchMedia('(prefers-color-scheme: dark)').matches;
document.documentElement.classList.toggle('dark',d);}catch(e){}})();`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-screen bg-bg-void text-text-dim antialiased">
        {children}
      </body>
    </html>
  );
}
