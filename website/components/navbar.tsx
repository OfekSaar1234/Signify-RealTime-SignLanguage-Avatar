"use client"

import { motion } from "framer-motion"
import { Download, Menu, X, ExternalLink, Github } from "lucide-react"
import { useState, useEffect } from "react"

const navLinks = [
  { label: "How it Works", href: "#how-it-works" },
  { label: "Installation", href: "#installation" },
  { label: "Data", href: "#data" },
]

export function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20)
    }
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled ? "py-4" : "py-8"
      }`}
    >
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <nav
          className={`relative flex items-center justify-between rounded-full px-6 py-3 transition-all duration-500 ${
            scrolled
              ? "bg-background/80 blur-backdrop subtle-border shadow-2xl"
              : "bg-transparent"
          }`}
        >
          {/* Logo */}
          <motion.a
            href="#"
            whileHover={{ opacity: 0.7 }}
            className="flex items-center gap-2 z-10"
          >
            <span className="font-serif italic text-2xl font-semibold text-blue-500">
              signify
            </span>
          </motion.a>

          {/* Desktop nav links */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link, i) => (
              <motion.a
                key={link.label}
                href={link.href}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 + i * 0.1, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                {link.label}
              </motion.a>
            ))}
          </div>

          {/* Right side: Actions */}
          <div className="hidden md:flex items-center gap-4 z-10">
            <motion.a
              href="https://github.com/OfekSaar1234/Signify-RealTime-SignLanguage-Avatar"
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted-foreground hover:text-foreground transition-colors p-2"
            >
              <Github size={20} />
            </motion.a>
            
            <motion.a
              href="#download"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="flex items-center gap-2 bg-primary text-primary-foreground px-5 py-2.5 rounded-full text-sm font-bold tracking-wide transition-all shadow-[0_0_20px_rgba(var(--primary)_/_0.3)] hover:shadow-[0_0_30px_rgba(var(--primary)_/_0.5)]"
            >
              Download
              <Download size={16} />
            </motion.a>
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden z-10 p-2 text-foreground"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </nav>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="absolute top-full left-6 right-6 mt-4 md:hidden rounded-3xl bg-background/95 blur-backdrop subtle-border p-6 shadow-2xl"
          >
            <div className="flex flex-col gap-6">
              {navLinks.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="text-lg font-medium text-foreground hover:text-primary transition-colors"
                >
                  {link.label}
                </a>
              ))}
              <div className="h-px bg-border w-full my-2" />
              <a
                href="https://github.com/OfekSaar1234/Signify-RealTime-SignLanguage-Avatar"
                className="flex items-center gap-2 text-lg font-medium text-foreground"
              >
                <Github size={20} />
                GitHub
              </a>
              <a
                href="#download"
                className="flex items-center justify-center gap-2 bg-primary text-primary-foreground px-6 py-4 rounded-full text-lg font-bold w-full mt-4"
              >
                <Download size={20} />
                Download for Windows
              </a>
            </div>
          </motion.div>
        )}
      </div>
    </motion.header>
  )
}
