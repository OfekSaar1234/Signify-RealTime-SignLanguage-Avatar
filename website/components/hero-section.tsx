"use client"

import { motion } from "framer-motion"
import { Download, ArrowRight, Github } from "lucide-react"

const expoEase = [0.16, 1, 0.3, 1] as const

export function HeroSection() {
  return (
    <section id="hero" className="relative w-full min-h-[90vh] flex items-center px-6 lg:px-8 pt-32 pb-20 overflow-hidden">
      
      {/* Refined background elements */}
      <div className="absolute top-0 right-0 -mr-[20%] -mt-[10%] w-[70vw] h-[70vw] rounded-full bg-primary/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 -ml-[10%] -mb-[10%] w-[50vw] h-[50vw] rounded-full bg-secondary/5 blur-[100px] pointer-events-none" />
      
      <div className="mx-auto max-w-7xl w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Left Column: Typography & Action */}
          <div className="lg:col-span-7 flex flex-col items-start text-left z-10">
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1, ease: expoEase }}
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-secondary text-secondary-foreground text-sm font-medium mb-8"
            >
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              Real-Time Accessibility
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1.2, delay: 0.1, ease: expoEase }}
              className="text-fluid-1 text-balance text-foreground mb-6"
            >
              Every meeting, <br className="hidden md:block" />
              now accessible in <span className="text-primary italic pr-2">real-time.</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1.2, delay: 0.2, ease: expoEase }}
              className="text-lg sm:text-xl text-muted-foreground max-w-2xl mb-12 leading-relaxed"
            >
              Signify captures system audio and broadcasts a highly responsive 3D signing avatar directly into Zoom or any conferencing software, empowering the deaf and hard of hearing community.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1.2, delay: 0.3, ease: expoEase }}
              className="flex flex-col sm:flex-row items-center gap-6 w-full sm:w-auto"
            >
              <motion.a
                href="#download"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full sm:w-auto flex items-center justify-center gap-3 bg-foreground text-background px-8 py-4 rounded-full text-lg font-bold tracking-wide transition-all hover:bg-foreground/90"
              >
                Download for Windows
                <Download size={20} />
              </motion.a>
              
              <a
                href="https://github.com/OfekSaar1234/Signify-RealTime-SignLanguage-Avatar"
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-center gap-2 text-foreground font-medium hover:text-primary transition-colors"
              >
                <Github size={20} />
                View Source
                <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
              </a>
            </motion.div>
          </div>

          {/* Right Column: Visual / Avatar Placeholder */}
          <div className="lg:col-span-5 relative z-10 w-full h-[500px] lg:h-[700px] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.9, filter: "blur(20px)" }}
              animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
              transition={{ duration: 1.5, delay: 0.4, ease: expoEase }}
              className="relative w-full h-full rounded-[2.5rem] bg-secondary/30 subtle-border overflow-hidden flex items-center justify-center"
            >
              {/* Abstract structural grid for the avatar area */}
              <div className="absolute inset-0 opacity-10" 
                style={{ backgroundImage: "radial-gradient(circle at 2px 2px, currentColor 1px, transparent 0)", backgroundSize: "32px 32px" }}
              />
              
              <div className="relative text-center px-6">
                <div className="w-24 h-24 mx-auto mb-6 rounded-full border border-primary/30 flex items-center justify-center animate-[spin_10s_linear_infinite]">
                  <div className="w-16 h-16 rounded-full border border-primary border-t-transparent animate-[spin_3s_linear_infinite_reverse]" />
                </div>
                <h3 className="font-display font-medium text-xl text-foreground mb-2">Sign Avatar Stream</h3>
                <p className="text-muted-foreground text-sm max-w-xs mx-auto">
                  Rendering 3D model with real-time WASAPI audio interception
                </p>
              </div>
            </motion.div>
          </div>
          
        </div>
      </div>
    </section>
  )
}
