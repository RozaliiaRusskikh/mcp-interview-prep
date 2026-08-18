import { NavLink, Outlet } from "react-router-dom";
import { TABS } from "../constants/nav";

export default function Layout() {
  return (
    <div className="min-h-screen px-4">
      <div className="max-w-175 mx-auto">
        <header className="pt-8 pb-6 flex items-start gap-8">
          <div className="flex-1">
            <p className="font-mono text-xs tracking-[0.18em] uppercase text-ink/60">
              <span>Roza Russkikh</span>
              <span> · </span>
              <a
                href="mailto:rrrusskikh@gmail.com"
                className="cursor-pointer transition-colors hover:text-ink normal-case tracking-normal focus-visible:outline-2 focus-visible:outline-ledger"
              >
                rrrusskikh@gmail.com
              </a>
              <span> · </span>
              <a
                href="tel:+16503156519"
                className="cursor-pointer transition-colors hover:text-ink normal-case tracking-normal focus-visible:outline-2 focus-visible:outline-ledger"
              >
                +1 650 315 6519
              </a>
            </p>
            <div className="flex flex-wrap gap-4 mt-3">
              <a
                href="https://www.linkedin.com/in/roza-russkikh/"
                target="_blank"
                rel="noopener noreferrer"
                className="font-mono font-medium text-xs uppercase tracking-wide text-ledger cursor-pointer border-b border-transparent transition-colors hover:border-ledger focus-visible:outline-2 focus-visible:outline-ledger"
              >
                LinkedIn ↗
              </a>
              <a
                href="https://github.com/RozaliiaRusskikh"
                target="_blank"
                rel="noopener noreferrer"
                className="font-mono font-medium text-xs uppercase tracking-wide text-ledger cursor-pointer border-b border-transparent transition-colors hover:border-ledger focus-visible:outline-2 focus-visible:outline-ledger"
              >
                GitHub ↗
              </a>
              <a
                href="/resume.pdf"
                download="Roza_Russkikh_Resume.pdf"
                className="font-mono font-medium text-xs uppercase tracking-wide text-ledger cursor-pointer border-b border-transparent transition-colors hover:border-ledger focus-visible:outline-2 focus-visible:outline-ledger"
              >
                Resume ↓
              </a>
            </div>
            <p className="font-script text-xl sm:text-4xl text-ink/80 leading-none mt-4">
              <strong className="text-ink">Software Engineer, </strong>
              always curious, loves solving problems that actually matter, and
              happiest working with a team while staying independent.
            </p>
          </div>
          <div className="hidden sm:block h-60 w-40 shrink-0 rotate-3 rounded-sm bg-card p-2 pb-9 ring-1 ring-ink/10 shadow-[0_10px_20px_-8px_rgba(30,42,58,0.45)] transition-all duration-300 hover:rotate-1 hover:-translate-y-1 hover:shadow-[0_14px_26px_-8px_rgba(30,42,58,0.5)]">
            <div className="relative h-full w-full overflow-hidden rounded-[1px] bg-ink/5">
              <img
                src="/roza_avatar.jpg"
                alt="Roza Russkikh"
                className="absolute inset-0 h-full w-full object-contain"
              />
            </div>
          </div>
        </header>

        <nav className="flex gap-6 border-b border-ink/15 pb-3 mb-8">
          {TABS.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              end={tab.end}
              className={({ isActive }) =>
                `font-mono text-xs uppercase tracking-wide cursor-pointer transition-colors focus-visible:outline-2 focus-visible:outline-ledger ${
                  isActive
                    ? "text-ink border-b-2 border-ledger pb-3 -mb-3"
                    : "text-ink/50 hover:text-ink"
                }`
              }
            >
              {tab.label}
            </NavLink>
          ))}
        </nav>

        <main className="flex flex-col gap-8 pb-32">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
