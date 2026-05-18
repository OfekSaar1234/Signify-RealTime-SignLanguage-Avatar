"use client"

import { motion, useScroll, useTransform } from "framer-motion"
import { useEffect, useState, useRef } from "react"

// Sign animation keyframes for different words
const signAnimations = {
  hello: [
    { leftHand: { x: 20, y: 0, rotation: 0 }, rightHand: { x: -20, y: -40, rotation: 15 }, label: "Hello" },
    { leftHand: { x: 20, y: 0, rotation: 0 }, rightHand: { x: 0, y: -50, rotation: 30 }, label: "Hello" },
    { leftHand: { x: 20, y: 0, rotation: 0 }, rightHand: { x: 20, y: -40, rotation: 15 }, label: "Hello" },
  ],
  how: [
    { leftHand: { x: -30, y: -20, rotation: -20 }, rightHand: { x: 30, y: -20, rotation: 20 }, label: "How" },
    { leftHand: { x: -20, y: -40, rotation: -30 }, rightHand: { x: 20, y: -40, rotation: 30 }, label: "How" },
    { leftHand: { x: -30, y: -20, rotation: -20 }, rightHand: { x: 30, y: -20, rotation: 20 }, label: "How" },
  ],
  install: [
    { leftHand: { x: -10, y: -30, rotation: 0 }, rightHand: { x: 10, y: -30, rotation: 0 }, label: "Install" },
    { leftHand: { x: -10, y: -50, rotation: -10 }, rightHand: { x: 10, y: -10, rotation: 10 }, label: "Install" },
    { leftHand: { x: -10, y: -30, rotation: 0 }, rightHand: { x: 10, y: -30, rotation: 0 }, label: "Install" },
  ],
  data: [
    { leftHand: { x: -40, y: -20, rotation: 45 }, rightHand: { x: 40, y: -20, rotation: -45 }, label: "Data" },
    { leftHand: { x: -30, y: -30, rotation: 30 }, rightHand: { x: 30, y: -30, rotation: -30 }, label: "Data" },
    { leftHand: { x: -40, y: -20, rotation: 45 }, rightHand: { x: 40, y: -20, rotation: -45 }, label: "Data" },
  ],
  welcome: [
    { leftHand: { x: -50, y: -10, rotation: -30 }, rightHand: { x: 50, y: -10, rotation: 30 }, label: "Welcome" },
    { leftHand: { x: -30, y: -30, rotation: -15 }, rightHand: { x: 30, y: -30, rotation: 15 }, label: "Welcome" },
    { leftHand: { x: 0, y: -40, rotation: 0 }, rightHand: { x: 0, y: -40, rotation: 0 }, label: "Welcome" },
  ],
}

type SignType = keyof typeof signAnimations

interface SignAvatarProps {
  className?: string
}

export function SignAvatar({ className = "" }: SignAvatarProps) {
  const [currentSign, setCurrentSign] = useState<SignType>("welcome")
  const [keyframe, setKeyframe] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)

  // Detect which section is in view
  useEffect(() => {
    const handleScroll = () => {
      const sections = [
        { id: "hero", sign: "welcome" as SignType },
        { id: "how-it-works", sign: "how" as SignType },
        { id: "installation", sign: "install" as SignType },
        { id: "data", sign: "data" as SignType },
      ]

      const scrollY = window.scrollY + window.innerHeight / 2

      for (const section of sections) {
        const element = document.getElementById(section.id)
        if (element) {
          const rect = element.getBoundingClientRect()
          const top = rect.top + window.scrollY
          const bottom = top + rect.height

          if (scrollY >= top && scrollY <= bottom) {
            if (currentSign !== section.sign) {
              setCurrentSign(section.sign)
              setKeyframe(0)
            }
            break
          }
        }
      }
    }

    window.addEventListener("scroll", handleScroll)
    handleScroll() // Initial check
    return () => window.removeEventListener("scroll", handleScroll)
  }, [currentSign])

  // Animate through keyframes
  useEffect(() => {
    const interval = setInterval(() => {
      setKeyframe((prev) => (prev + 1) % signAnimations[currentSign].length)
    }, 600)
    return () => clearInterval(interval)
  }, [currentSign])

  const currentFrame = signAnimations[currentSign][keyframe]

  return (
    <div
      ref={containerRef}
      className={`fixed z-50 top-16 right-2 md:top-auto md:bottom-8 md:right-8 ${className}`}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.8, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 1 }}
        className="relative"
      >
        {/* Avatar container - smaller on mobile, larger on desktop */}
        <div className="relative w-20 h-24 md:w-44 md:h-56 lg:w-52 lg:h-64">
          {/* Avatar body */}
          <svg
            viewBox="-20 0 140 130"
            className="relative w-full h-full drop-shadow-2xl overflow-visible"
          >
            {/* Body */}
            <ellipse
              cx="50"
              cy="100"
              rx="28"
              ry="22"
              className="fill-primary/80"
            />
            
            {/* Neck */}
            <rect
              x="43"
              y="62"
              width="14"
              height="18"
              rx="3"
              className="fill-amber-200 dark:fill-amber-300"
            />
            
            {/* Head */}
            <ellipse
              cx="50"
              cy="40"
              rx="26"
              ry="28"
              className="fill-amber-200 dark:fill-amber-300"
            />
            
            {/* Hair */}
            <ellipse
              cx="50"
              cy="22"
              rx="20"
              ry="12"
              className="fill-amber-800 dark:fill-amber-900"
            />
            
            {/* Eyes */}
            <ellipse cx="40" cy="40" rx="4" ry="5" className="fill-foreground/80" />
            <ellipse cx="60" cy="40" rx="4" ry="5" className="fill-foreground/80" />
            <circle cx="41" cy="39" r="1.5" className="fill-white" />
            <circle cx="61" cy="39" r="1.5" className="fill-white" />
            
            {/* Eyebrows */}
            <path d="M 35 32 Q 40 30 45 32" fill="none" className="stroke-amber-800 dark:stroke-amber-900" strokeWidth="2" strokeLinecap="round" />
            <path d="M 55 32 Q 60 30 65 32" fill="none" className="stroke-amber-800 dark:stroke-amber-900" strokeWidth="2" strokeLinecap="round" />
            
            {/* Smile */}
            <path
              d="M 40 52 Q 50 60 60 52"
              fill="none"
              className="stroke-amber-800 dark:stroke-amber-900"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
            
            {/* Left Hand */}
            <motion.g
              animate={{
                x: currentFrame.leftHand.x,
                y: currentFrame.leftHand.y,
                rotate: currentFrame.leftHand.rotation,
              }}
              transition={{ duration: 0.4, ease: "easeInOut" }}
            >
              {/* Arm */}
              <ellipse
                cx="22"
                cy="90"
                rx="10"
                ry="22"
                className="fill-primary/80"
              />
              {/* Hand */}
              <circle
                cx="22"
                cy="68"
                r="10"
                className="fill-amber-200 dark:fill-amber-300"
              />
              {/* Fingers */}
              <ellipse cx="15" cy="60" rx="2.5" ry="6" className="fill-amber-200 dark:fill-amber-300" />
              <ellipse cx="22" cy="57" rx="2.5" ry="7" className="fill-amber-200 dark:fill-amber-300" />
              <ellipse cx="29" cy="60" rx="2.5" ry="6" className="fill-amber-200 dark:fill-amber-300" />
            </motion.g>
            
            {/* Right Hand */}
            <motion.g
              animate={{
                x: currentFrame.rightHand.x,
                y: currentFrame.rightHand.y,
                rotate: currentFrame.rightHand.rotation,
              }}
              transition={{ duration: 0.4, ease: "easeInOut" }}
            >
              {/* Arm */}
              <ellipse
                cx="78"
                cy="90"
                rx="10"
                ry="22"
                className="fill-primary/80"
              />
              {/* Hand */}
              <circle
                cx="78"
                cy="68"
                r="10"
                className="fill-amber-200 dark:fill-amber-300"
              />
              {/* Fingers */}
              <ellipse cx="71" cy="60" rx="2.5" ry="6" className="fill-amber-200 dark:fill-amber-300" />
              <ellipse cx="78" cy="57" rx="2.5" ry="7" className="fill-amber-200 dark:fill-amber-300" />
              <ellipse cx="85" cy="60" rx="2.5" ry="6" className="fill-amber-200 dark:fill-amber-300" />
            </motion.g>
          </svg>
        </div>

        {/* Current sign label - hidden on mobile */}
        <motion.div
          key={currentSign}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute -bottom-8 left-1/2 -translate-x-1/2 whitespace-nowrap hidden md:block"
        >
          <span className="text-xs font-medium text-primary bg-card px-3 py-1 rounded-full border border-primary/30 shadow-lg">
            Signing: {currentFrame.label}
          </span>
        </motion.div>
      </motion.div>
    </div>
  )
}
