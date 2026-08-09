"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Chrome, Youtube, Twitch, PlaySquare } from "lucide-react"

const fadeUp = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } }
}

export function ChromeExtensionSection() {
  const [activeTab, setActiveTab] = useState<"spongebob" | "twitch" | "kids">("spongebob");

  return (
    <section className="relative w-full py-24 px-6 lg:px-8 bg-background overflow-hidden border-t border-border/10">
      <div className="absolute top-1/2 left-0 -translate-y-1/2 -translate-x-1/4 w-[40vw] h-[40vw] rounded-full bg-primary/5 blur-[120px] pointer-events-none" />
      
      <div className="mx-auto max-w-7xl">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center"
        >
          {/* Visual Side */}
          <div className="relative order-2 lg:order-1">
            <motion.div variants={fadeUp} className="relative w-full aspect-[4/3] rounded-[2rem] bg-secondary/30 border border-border/50 overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-tr from-background/80 via-transparent to-transparent z-10" />
              
              {/* Screenshots Container */}
              <div className="absolute inset-0 z-0 bg-black">
                <img 
                  src="/images/youtubeSpongbob.png" 
                  alt="YouTube Extension Overlay"
                  className={`absolute inset-0 w-full h-full object-contain transition-opacity duration-500 ${activeTab === "spongebob" ? "opacity-100 z-10" : "opacity-0 z-0"}`} 
                />
                <img 
                  src="/images/kidsyoutube.png" 
                  alt="Kids YouTube Extension Overlay"
                  className={`absolute inset-0 w-full h-full object-contain transition-opacity duration-500 ${activeTab === "kids" ? "opacity-100 z-10" : "opacity-0 z-0"}`} 
                />
                <img 
                  src="/images/twitchpng.png" 
                  alt="Twitch Extension Overlay"
                  className={`absolute inset-0 w-full h-full object-contain transition-opacity duration-500 ${activeTab === "twitch" ? "opacity-100 z-10" : "opacity-0 z-0"}`} 
                />
              </div>

            </motion.div>

            {/* Interactive Tabs */}
            <div className="absolute -top-6 -left-4 sm:-left-8 z-20 flex flex-col gap-3">
              <div 
                onClick={() => setActiveTab("spongebob")}
                className={`bg-background/95 backdrop-blur-md border ${activeTab === 'spongebob' ? 'border-primary shadow-lg shadow-primary/20' : 'border-border/50'} rounded-xl p-3 flex items-center gap-3 transform hover:scale-105 transition-all duration-300 hover:bg-secondary cursor-pointer`}
              >
                <div className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center">
                  <Youtube className="w-4 h-4 text-red-500" />
                </div>
                <div className="text-sm font-medium">Spongebob (YouTube)</div>
              </div>
              <div 
                onClick={() => setActiveTab("kids")}
                className={`bg-background/95 backdrop-blur-md border ${activeTab === 'kids' ? 'border-primary shadow-lg shadow-primary/20' : 'border-border/50'} rounded-xl p-3 flex items-center gap-3 transform hover:scale-105 transition-all duration-300 hover:bg-secondary cursor-pointer`}
              >
                <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
                  <PlaySquare className="w-4 h-4 text-green-500" />
                </div>
                <div className="text-sm font-medium">Kids (YouTube)</div>
              </div>
              <div 
                onClick={() => setActiveTab("twitch")}
                className={`bg-background/95 backdrop-blur-md border ${activeTab === 'twitch' ? 'border-primary shadow-lg shadow-primary/20' : 'border-border/50'} rounded-xl p-3 flex items-center gap-3 transform hover:scale-105 transition-all duration-300 hover:bg-secondary cursor-pointer`}
              >
                <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center">
                  <Twitch className="w-4 h-4 text-purple-500" />
                </div>
                <div className="text-sm font-medium">Twitch Stream</div>
              </div>
            </div>
          </div>

          {/* Content Side */}
          <div className="order-1 lg:order-2 flex flex-col items-start text-left z-10">
            <motion.div variants={fadeUp} className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
              <Chrome size={14} />
              Browser Extension
            </motion.div>

            <motion.h2 variants={fadeUp} className="text-3xl md:text-5xl font-medium tracking-tight text-foreground mb-6">
              Signify <span className="text-primary italic">Everywhere</span> you browse.
            </motion.h2>

            <motion.p variants={fadeUp} className="text-lg text-muted-foreground mb-8 leading-relaxed max-w-xl">
              Take the Signify 3D Avatar with you across the web. Our lightweight Chrome Extension seamlessly overlays the real-time sign language interpreter directly onto your favorite video platforms. 
              Whether you're watching a stream on Twitch, a video on YouTube, or catching up on CBS News, Signify intercepts the audio and brings accessibility right to your screen.
            </motion.p>

            <motion.div variants={fadeUp} className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full">
              <div className="p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-colors">
                <Youtube className="w-6 h-6 text-foreground mb-3" />
                <h4 className="font-medium text-foreground mb-1">YouTube Support</h4>
                <p className="text-sm text-muted-foreground">Automatically injects the avatar over any YouTube video. Incredibly useful for young kids who are learning sign language but don't know how to read captions yet!</p>
              </div>
              <div className="p-4 rounded-2xl bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-colors">
                <Twitch className="w-6 h-6 text-foreground mb-3" />
                <h4 className="font-medium text-foreground mb-1">Twitch Integration</h4>
                <p className="text-sm text-muted-foreground">Follow live streams with real-time translation overlay.</p>
              </div>
            </motion.div>

            <motion.div variants={fadeUp} className="mt-8 flex flex-col items-start gap-4">
              <a 
                href="/signify-extension.zip"
                download="signify-extension.zip"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-full bg-foreground text-background font-medium hover:bg-foreground/90 transition-colors"
              >
                <Chrome size={18} />
                Download Chrome Extension (.zip)
              </a>
              
              <div className="bg-secondary/20 border border-border/40 rounded-xl p-4 text-sm text-muted-foreground w-full max-w-md">
                <h4 className="font-semibold text-foreground mb-2">How to install (Developer Mode):</h4>
                <ol className="list-decimal list-inside space-y-1.5 ml-1">
                  <li>Extract the downloaded <code className="text-xs bg-black/20 px-1 rounded">.zip</code> file.</li>
                  <li>Go to <code className="text-xs bg-black/20 px-1 rounded select-all">chrome://extensions</code> in your browser.</li>
                  <li>Enable <strong>Developer mode</strong> (toggle in top right).</li>
                  <li>Click <strong>Load unpacked</strong> and select the extracted folder.</li>
                </ol>
              </div>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
