"use client"

import { Github, Linkedin, ArrowUpRight } from "lucide-react"

export function Footer() {
  return (
    <footer className="w-full bg-background border-t border-border pt-24 pb-12 px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mb-24">
          
          {/* Brand & Mission */}
          <div>
            <h2 className="font-serif italic text-4xl font-semibold text-blue-500 mb-6">
              signify
            </h2>
            <p className="text-muted-foreground text-lg max-w-sm">
              Bridging the communication gap through real-time, local-first sign language translation.
            </p>
          </div>

          {/* Links Grid */}
          <div className="grid grid-cols-2 gap-8 md:justify-end">
            <div className="flex flex-col gap-4">
              <span className="text-sm font-mono text-muted-foreground uppercase tracking-widest mb-2">Project</span>
              <a href="https://github.com/OfekSaar1234/Signify-RealTime-SignLanguage-Avatar" target="_blank" rel="noopener noreferrer" className="group flex items-center gap-1 text-foreground hover:text-primary transition-colors">
                Source Code <ArrowUpRight size={14} className="opacity-50 group-hover:opacity-100 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
              </a>
              <a href="#demo" className="text-foreground hover:text-primary transition-colors">Demo</a>
              <a href="#how-it-works" className="text-foreground hover:text-primary transition-colors">Architecture</a>
            </div>
            <div className="flex flex-col gap-4">
              <span className="text-sm font-mono text-muted-foreground uppercase tracking-widest mb-2">Creators</span>
              <a href="#" className="flex items-center gap-2 text-foreground hover:text-primary transition-colors">
                Ofek Saar
              </a>
              <a href="#" className="flex items-center gap-2 text-foreground hover:text-primary transition-colors">
                Ori Ratzabi
              </a>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-8 border-t border-border/50">
          <p className="text-sm font-mono text-muted-foreground uppercase tracking-widest">
            &copy; 2026 Signify
          </p>
          <div className="flex items-center gap-6">
            <a href="https://github.com/OfekSaar1234/Signify-RealTime-SignLanguage-Avatar" target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground transition-colors">
              <Github size={20} />
            </a>
            <a href="#" className="text-muted-foreground hover:text-foreground transition-colors">
              <Linkedin size={20} />
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}
