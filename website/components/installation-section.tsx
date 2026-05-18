"use client"

import { motion } from "framer-motion"
import { Download, Terminal, Video } from "lucide-react"

const expoEase = [0.16, 1, 0.3, 1] as const

const steps = [
  {
    num: "01",
    title: "Install Virtual Camera",
    desc: "Signify relies on the OBS Virtual Camera driver to broadcast the avatar feed. Install OBS Studio and ensure the Virtual Camera component is enabled during setup.",
    action: "Download OBS Studio",
    href: "https://obsproject.com/download",
    icon: Download,
  },
  {
    num: "02",
    title: "Launch Signify Engine",
    desc: "Run the standalone executable. The engine will automatically interface with WASAPI to capture system audio and initialize the local NLP models. No cloud connection required.",
    command: ".\\Signify.exe --start-engine",
    icon: Terminal,
  },
  {
    num: "03",
    title: "Configure Conference App",
    desc: "Join your meeting (Zoom, Teams, etc.). Select 'OBS Virtual Camera' as your video input. The avatar will automatically animate in real-time based on the ongoing conversation.",
    action: "View Setup Guide",
    href: "#",
    icon: Video,
  },
]

export function InstallationSection() {
  return (
    <section id="installation" className="w-full py-32 bg-foreground text-background">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: false, margin: "-100px" }}
          transition={{ duration: 1, ease: expoEase }}
          className="mb-20"
        >
          <h2 className="text-fluid-2 text-background mb-6">
            Deployment <span className="font-serif italic pr-2 text-background/70">Protocol</span>
          </h2>
          <p className="text-xl text-background/60 max-w-2xl leading-relaxed">
            A frictionless setup process designed to get the accessibility engine running on your local machine in under three minutes.
          </p>
        </motion.div>

        {/* Linear step layout instead of generic accordions */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {steps.map((step, index) => (
            <motion.div
              key={step.num}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: false, margin: "-100px" }}
              transition={{ duration: 1, delay: index * 0.15, ease: expoEase }}
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
                  className="inline-flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-background hover:text-primary transition-colors"
                >
                  {step.action}
                  <span className="text-xl leading-none">&rarr;</span>
                </a>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
