"use client"

import { motion } from "framer-motion"
import { Download, ArrowRight, Github, Twitch, Youtube, Chrome, Tv, Video } from "lucide-react"

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
              now accessible <span className="text-primary italic pr-2">everywhere.</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1.2, delay: 0.2, ease: expoEase }}
              className="text-lg sm:text-xl text-muted-foreground max-w-2xl mb-8 leading-relaxed"
            >
              Signify captures audio and broadcasts a highly responsive 3D signing avatar directly into Zoom, YouTube, Twitch streams, and Live TV—empowering the deaf and hard of hearing community across all platforms.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1.2, delay: 0.25, ease: expoEase }}
              className="flex items-center gap-4 mb-12 text-muted-foreground"
            >
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary/50 border border-border/50 text-sm">
                <Video size={16} /> <span className="hidden sm:inline">Zoom</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary/50 border border-border/50 text-sm">
                <Chrome size={16} /> <span className="hidden sm:inline">Chrome</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary/50 border border-border/50 text-sm">
                <Youtube size={16} /> <span className="hidden sm:inline">YouTube</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary/50 border border-border/50 text-sm">
                <Twitch size={16} /> <span className="hidden sm:inline">Twitch</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary/50 border border-border/50 text-sm">
                <Tv size={16} /> <span className="hidden sm:inline">Smart TV</span>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1.2, delay: 0.3, ease: expoEase }}
              className="flex flex-col sm:flex-row items-center gap-6 w-full sm:w-auto"
            >
              <motion.a
                href="/Signify.zip"
                download="Signify.zip"
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
              className="relative w-full h-full rounded-[2.5rem] bg-secondary/30 subtle-border overflow-hidden flex items-center justify-center shadow-2xl"
            >
              <img 
                src="/images/ZOOM.png" 
                alt="Signify Zoom Meeting Integration" 
                className="absolute inset-0 w-full h-full object-cover" 
              />
            </motion.div>
          </div>
          
        </div>
      </div>
    </section>
  )
}
