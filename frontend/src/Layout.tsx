import { NavLink, Outlet } from "react-router-dom";

const TABS = [
  { to: "/", label: "Chat", end: true },
  { to: "/recommendations", label: "Recommendations", end: false },
];

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col items-center px-4">
      <header className="w-full max-w-175 pt-14 pb-6 flex items-start gap-4">
        <div className="flex-1">
          <p className="font-mono text-xs tracking-[0.18em] uppercase text-ink/60">
            Roza Russkikh · Skills showcase
          </p>
          <div className="flex gap-4 mt-3">
            <a
              href="https://www.linkedin.com/in/roza-russkikh/"
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-xs uppercase tracking-wide text-ledger cursor-pointer hover:underline"
            >
              LinkedIn ↗
            </a>
            <a
              href="https://github.com/RozaliiaRusskikh"
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-xs uppercase tracking-wide text-ledger cursor-pointer hover:underline"
            >
              GitHub ↗
            </a>
            <a
              href="/resume.pdf"
              download="Roza_Russkikh_Resume.pdf"
              className="font-mono text-xs uppercase tracking-wide text-ledger cursor-pointer hover:underline"
            >
              Resume ↓
            </a>
          </div>
          <p className="font-display text-xl text-ink/85 leading-snug mt-6 max-w-[36ch]">
            Teacher, then QA, now full-stack and AI engineer: I build software that actually helps people.
          </p>
        </div>
        <img
          src="/roza-bot-avatar.png"
          alt="Roza Russkikh"
          className="hidden sm:block w-32 h-32 object-cover border border-ink/20 shadow-sm rotate-2 shrink-0"
        />
      </header>

      <nav className="w-full max-w-175 flex gap-6 border-b border-ink/15 pb-3 mb-8">
        {TABS.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            end={tab.end}
            className={({ isActive }) =>
              `font-mono text-xs uppercase tracking-wide cursor-pointer transition-colors ${
                isActive ? "text-ink border-b-2 border-ledger pb-3 -mb-3" : "text-ink/50 hover:text-ink"
              }`
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>

      <main className="w-full max-w-175 flex flex-col gap-8 pb-32">
        <Outlet />
      </main>
    </div>
  );
}
