"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

function linkClasses(active: boolean) {
  return active
    ? "text-sm font-medium text-slate-900"
    : "text-sm font-medium text-slate-500 hover:text-slate-900";
}

export default function NavBar() {
  const pathname = usePathname();

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link href="/series" className="text-lg font-semibold text-slate-900">
          AI Cartoon Studio
        </Link>
        <nav className="flex gap-6">
          <Link href="/series" className={linkClasses(pathname.startsWith("/series"))}>
            Series
          </Link>
          <Link href="/settings" className={linkClasses(pathname.startsWith("/settings"))}>
            Settings
          </Link>
        </nav>
      </div>
    </header>
  );
}
