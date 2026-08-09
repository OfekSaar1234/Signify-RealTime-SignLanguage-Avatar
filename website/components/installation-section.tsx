"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Download, Terminal, Video, Monitor, Chrome } from "lucide-react"

const expoEase = [0.16, 1, 0.3, 1] as const

const appSteps = [
  {
    num: "01",
    title: "Install Virtual Camera",
    desc: "Signify relies on the OBS Virtual Camera driver to broadcast the avatar feed. Install OBS Studio and ensure the Virtual Camera component is enabled.",
    action: "Download OBS Studio",
    href: "https://obsproject.com/download",
    icon: Download,
  },
  {
    num: "02",
    title: "Launch Signify Engine",
    desc: "Run the standalone executable. The engine will automatically interface with WASAPI to capture system audio and initialize the local NLP models.",
    command: ".\\Signify.exe --start-engine",
    icon: Terminal,
  },
  {
    num: "03",
    title: "Configure App",
    desc: "Join your meeting (Zoom, Teams). Select 'OBS Virtual Camera' as your video input. The avatar will automatically animate in real-time.",
    action: "View Setup Guide",
    href: "#",
    icon: Video,
  },
]

const extSteps = [
  {
    num: "01",
    title: "Download Extension",
    desc: "Get the latest version of the Signify Chrome Extension from our GitHub repository and extract the ZIP file to a folder.",
    action: "Download ZIP",
    href: "https://github.com/OfekSaar1234/Signify-RealTime-SignLanguage-Avatar/tree/main/chrome-extension",
    icon: Download,
  },
  {
    num: "02",
    title: "Enable Developer Mode",
    desc: "Open your Chrome browser and navigate to the extensions page. Turn on the 'Developer mode' toggle in the top right corner.",
    command: "chrome://extensions",
    icon: Chrome,
  },
  {
    num: "03",
    title: "Load Unpacked",
    desc: "Click 'Load unpacked' and select the folder you extracted in Step 1. The Signify avatar is now ready to overlay on YouTube and Twitch!",
    action: "Start Browsing",
    href: "#",
    icon: Monitor,
  },
]

export function InstallationSection() {
  const [activeTab, setActiveTab] = useState<"desktop" | "extension">("desktop")

  const currentSteps = activeTab === "desktop" ? appSteps : extSteps

  return (
    <section id="installation" className="w-full py-32 bg-foreground text-background">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: false, margin: "-100px" }}
          transition={{ duration: 1, ease: expoEase }}
          className="mb-12 flex flex-col lg:flex-row justify-between items-start lg:items-end gap-8"
        >
          <div>
            <h2 className="text-fluid-2 text-background mb-6">
              Deployment <span className="font-serif italic pr-2 text-background/70">Protocol</span>
            </h2>
            <p className="text-xl text-background/60 max-w-2xl leading-relaxed">
              A frictionless setup process designed to get the accessibility engine running in under three minutes.
            </p>
          </div>

          {/* Tabs */}
          <div className="flex bg-background/10 p-1 rounded-full border border-background/20">
            <button
              onClick={() => setActiveTab("desktop")}
              className={`px-6 py-2.5 rounded-full text-sm font-medium transition-colors flex items-center gap-2 ${
                activeTab === "desktop" ? "bg-background text-foreground" : "text-background/60 hover:text-background"
              }`}
            >
              <Monitor size={16} />
              Desktop App
            </button>
            <button
              onClick={() => setActiveTab("extension")}
              className={`px-6 py-2.5 rounded-full text-sm font-medium transition-colors flex items-center gap-2 ${
                activeTab === "extension" ? "bg-background text-foreground" : "text-background/60 hover:text-background"
              }`}
            >
              <Chrome size={16} />
              Chrome Extension
            </button>
          </div>
        </motion.div>

        {/* Linear step layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 relative min-h-[300px]">
          <AnimatePresence mode="wait">
            {currentSteps.map((step, index) => (
              <motion.div
                key={activeTab + step.num}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.5, delay: index * 0.1, ease: expoEase }}
                className="flex flex-col border-t border-background/20 pt-8"
              >
                <div className="flex items-center justify-between mb-8">
                  <span className="font-display text-4xl font-light text-background/40">
                    {step.num}
                  </span>
                  <step.icon size={24} className="text-background/40" />
                </div>
                
                <h3 className="font-display font-medium text-2xl text-background mb-4">
                  {step.title}
                </h3>
                
                <p className="text-background/60 leading-relaxed mb-8 flex-grow">
                  {step.desc}
                </p>
                
                {step.command ? (
                  <div className="bg-background/10 rounded-lg p-4 font-mono text-sm text-background overflow-hidden whitespace-nowrap">
                    <span className="text-primary/80 mr-2">{">"}</span> 
                    {step.command}
                  </div>
                ) : (
                  <a
                    href={step.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-background hover:text-primary transition-colors"
                  >
                    {step.action}
                    <span className="text-xl leading-none">&rarr;</span>
                  </a>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </section>
  )
}
