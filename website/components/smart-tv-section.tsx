"use client"

import { motion } from "framer-motion"
import { Tv, Play, Settings, Wifi } from "lucide-react"

const fadeUp = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } }
}

export function SmartTvSection() {
  return (
    <section className="relative w-full py-24 px-6 lg:px-8 bg-secondary/10 overflow-hidden border-t border-border/10">
      <div className="absolute top-1/2 right-0 -translate-y-1/2 translate-x-1/4 w-[40vw] h-[40vw] rounded-full bg-primary/5 blur-[120px] pointer-events-none" />
      
      <div className="mx-auto max-w-7xl">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center"
        >
          {/* Content Side */}
          <div className="order-1 flex flex-col items-start text-left z-10">
            <motion.div variants={fadeUp} className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
              <Tv size={14} />
              Smart TV App
            </motion.div>

            <motion.h2 variants={fadeUp} className="text-3xl md:text-5xl font-medium tracking-tight text-foreground mb-6">
              Accessible <span className="text-primary italic">Broadcasting</span> on the big screen.
            </motion.h2>

            <motion.p variants={fadeUp} className="text-lg text-muted-foreground mb-8 leading-relaxed max-w-xl">
              Signify isn't just for PCs. We've built a dedicated LG webOS TV application that allows broadcasters to stream live TV with a real-time, WebSocket-powered sign language avatar overlay. Tune in to continuous news or custom broadcasts directly from your couch.
            </motion.p>

            <motion.div variants={fadeUp} className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full">
              <div className="p-4 rounded-2xl bg-background border border-border/50 hover:border-primary/50 transition-colors">
                <Wifi className="w-6 h-6 text-foreground mb-3" />
                <h4 className="font-medium text-foreground mb-1">WebSocket Streaming</h4>
                <p className="text-sm text-muted-foreground">Low-latency animation data streamed directly to the TV.</p>
              </div>
              <div className="p-4 rounded-2xl bg-background border border-border/50 hover:border-primary/50 transition-colors">
                <Settings className="w-6 h-6 text-foreground mb-3" />
                <h4 className="font-medium text-foreground mb-1">Playback Control</h4>
                <p className="text-sm text-muted-foreground">Adjust playback speed and customize the avatar position.</p>
              </div>
            </motion.div>

            <motion.div variants={fadeUp} className="mt-8">
              <a 
                href="/lg_tv_app/index.html"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-full bg-foreground text-background font-medium hover:bg-foreground/90 transition-colors"
              >
                <Tv size={18} />
                View TV App Preview
              </a>
            </motion.div>
          </div>

          {/* Visual Side */}
          <div className="relative order-2">
            <motion.div variants={fadeUp} className="relative w-full aspect-video rounded-[2rem] bg-secondary/30 border border-border/50 overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-bl from-background/80 via-transparent to-transparent z-10" />
              
              {/* TV Screenshot Container */}
              <div className="absolute inset-0 z-0 bg-black">
                <img 
                  src="/images/CBSNEWS.png" 
                  alt="LG webOS TV App Interface"
                  className="absolute inset-0 w-full h-full object-contain" 
                />
              </div>

              {/* Decorative TV UI */}
              <div className="absolute bottom-6 left-6 right-6 z-20">
                <div className="bg-background/90 backdrop-blur-md border border-border/50 rounded-2xl p-4 shadow-2xl transform translate-y-8 group-hover:translate-y-0 transition-transform duration-500">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
                        <Play className="w-5 h-5 text-primary-foreground ml-1" />
                      </div>
                      <div>
                        <div className="font-medium text-sm">SIGNIFY NEWS 24/7</div>
                        <div className="text-xs text-red-500 font-bold flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                          LIVE
                        </div>
                      </div>
                    </div>
                    <div className="px-3 py-1.5 rounded-full bg-secondary text-xs font-medium border border-border">
                      WS: Connected
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
