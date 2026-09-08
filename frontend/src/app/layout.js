
import "./globals.css";

export const metadata = {
  title: "LegalMind Reviewer",
  description: "LegalMind Phase 3 Reviewer Dashboard"
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
