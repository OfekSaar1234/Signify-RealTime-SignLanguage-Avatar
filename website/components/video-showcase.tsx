"use client"

import { useRef, useState } from "react"
import { motion, useInView } from "framer-motion"
import { Play, Pause, Maximize2, Volume2, VolumeX } from "lucide-react"

const expoEase = [0.16, 1, 0.3, 1] as const

export function VideoShowcase() {
  const sectionRef = useRef<HTMLElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const isInView = useInView(sectionRef, { once: false, margin: "-100px" })
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(true)
  const [showControls, setShowControls] = useState(true)

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause()
      } else {
        videoRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted
      setIsMuted(!isMuted)
    }
  }

  const toggleFullscreen = () => {
    if (videoRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen()
      } else {
        videoRef.current.requestFullscreen()
      }
    }
  }

  return (
    <section
      ref={sectionRef}
      id="demo"
      className="py-32 relative overflow-hidden bg-background"
    >
      <div className="mx-auto max-w-7xl px-6 lg:px-8 relative z-10">
        
        {/* Section header: Editorial style */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 1, ease: expoEase }}
          className="max-w-3xl mb-16"
        >
          <h2 className="text-fluid-2 text-foreground mb-6">
            Witness the <span className="text-primary italic pr-2">Translation</span>
          </h2>
          <p className="text-xl text-muted-foreground leading-relaxed">
            A raw, unfiltered look at Signify interpreting spoken English into expressive, 
            grammatically accurate American Sign Language in real-time.
          </p>
        </motion.div>

        {/* Cinematic Video container */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98, y: 40 }}
          animate={isInView ? { opacity: 1, scale: 1, y: 0 } : {}}
          transition={{ duration: 1.2, delay: 0.2, ease: expoEase }}
          className="relative w-full aspect-video group"
          onMouseEnter={() => setShowControls(true)}
          onMouseLeave={() => isPlaying && setShowControls(false)}
        >
          {/* Abstract background glow instead of standard shadow */}
          <div className="absolute inset-0 bg-primary/5 blur-[100px] pointer-events-none" />
          
          <div className="relative w-full h-full overflow-hidden bg-[#0A0A0A] rounded-[2rem] subtle-border shadow-2xl flex items-center justify-center">
            
            <video
              ref={videoRef}
              src="/showcase-video.mp4"
              className="w-full h-full object-cover opacity-90 transition-opacity duration-700"
              muted={isMuted}
              loop
              playsInline
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
            />
            
            {/* Play overlay - minimalist and sharp */}
            {!isPlaying && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="absolute inset-0 flex items-center justify-center bg-background/20 blur-backdrop cursor-pointer"
                onClick={togglePlay}
              >
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="w-24 h-24 rounded-full bg-foreground text-background flex items-center justify-center shadow-2xl"
                >
                  <Play className="w-8 h-8 ml-1" fill="currentColor" />
                </motion.div>
              </motion.div>
            )}
            
            {/* Minimalist Controls */}
            <motion.div
              initial={false}
              animate={{ opacity: showControls ? 1 : 0, y: showControls ? 0 : 10 }}
              transition={{ duration: 0.4, ease: expoEase }}
              className="absolute bottom-6 left-6 right-6 p-4 rounded-2xl bg-background/80 blur-backdrop subtle-border flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                <button
                  onClick={togglePlay}
                  className="text-foreground hover:text-primary transition-colors"
                >
                  {isPlaying ? <Pause size={24} /> : <Play size={24} fill="currentColor" />}
                </button>
                <div className="w-px h-6 bg-border" />
                <button
                  onClick={toggleMute}
                  className="text-foreground hover:text-primary transition-colors"
                >
                  {isMuted ? <VolumeX size={24} /> : <Volume2 size={24} />}
                </button>
              </div>
              <button
                onClick={toggleFullscreen}
                className="text-foreground hover:text-primary transition-colors"
              >
                <Maximize2 size={24} />
              </button>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
