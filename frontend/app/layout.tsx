import './globals.css';
import Sidebar from '@/components/Sidebar';

export const metadata = {
  title: 'FraudShield 2.0 — Temporal Graph Intelligence & AI Investigation',
  description: 'Evidence-driven financial fraud intelligence and investigation platform.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 flex min-h-screen">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0 overflow-x-hidden">
          {children}
        </div>
      </body>
    </html>
  );
}
