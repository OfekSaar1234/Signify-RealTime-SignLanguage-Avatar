"use client"

import { useRef } from "react"
import { motion, useScroll, useTransform } from "framer-motion"

const steps = [
  {
    num: "01",
    title: "Audio Interception",
    desc: "Using the WASAPI API, Signify captures high-fidelity system audio and microphone input directly at the OS level, completely bypassing generic web-audio limitations.",
  },
  {
    num: "02",
    title: "Instant Transcription",
    desc: "The dual audio streams are fed into an optimized speech-to-text pipeline, delivering lightning-fast English transcriptions with deep contextual awareness.",
  },
  {
    num: "03",
    title: "Grammar Translation",
    desc: "A local, specialized Natural Language Processing model restructures English sentences into accurate ASL syntax (Topic-Comment structure, facial expressions mapping).",
  },
  {
    num: "04",
    title: "Avatar Broadcast",
    desc: "The final translation triggers precise 3D bone animations. This visual stream is piped into Zoom as a seamless Virtual Camera.",
  },
]

export function HowItWorks() {
  const containerRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"],
  })

  // A subtle parallax effect on the background abstract shapes
  const yBg = useTransform(scrollYProgress, [0, 1], ["0%", "50%"])

  return (
    <section id="how-it-works" ref={containerRef} className="relative w-full py-32 bg-background overflow-hidden">
      
      <motion.div 
        style={{ y: yBg }} 
        className="absolute top-1/4 right-0 w-[40vw] h-[80vh] bg-primary/5 rounded-[100px] -rotate-12 blur-3xl pointer-events-none" 
      />

      <div className="mx-auto max-w-7xl px-6 lg:px-8 relative z-10">
        
        {/* Editorial Heading */}
        <div className="mb-24 md:mb-32">
          <h2 className="text-fluid-2 text-foreground">
            The <span className="font-serif italic pr-2">Pipeline</span>
          </h2>
        </div>

        {/* Asymmetric List replacing the generic cards */}
        <div className="flex flex-col gap-16 md:gap-32 relative">
          
          {/* Vertical connecting line */}
          <div className="hidden md:block absolute top-0 bottom-0 left-[2.25rem] w-px bg-border z-0" />

          {steps.map((step, i) => (
            <motion.div 
              key={step.num}
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: false, margin: "-100px" }}
              transition={{ duration: 1, ease: [0.16, 1, 0.3, 1], delay: i * 0.1 }}
              className="relative z-10 flex flex-col md:flex-row gap-8 md:gap-16 items-start"
            >
              {/* Number/Node */}
              <div className="flex-shrink-0 w-16 h-16 rounded-full bg-background subtle-border flex items-center justify-center shadow-xl">
                <span className="font-display font-bold text-xl text-primary">{step.num}</span>
              </div>
              
              {/* Content block */}
              <div className="flex-1 pt-2 max-w-3xl">
                <h3 className="font-display font-semibold text-3xl md:text-4xl text-foreground mb-6">
                  {step.title}
                </h3>
                <p className="text-lg md:text-xl text-muted-foreground leading-relaxed">
                  {step.desc}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
