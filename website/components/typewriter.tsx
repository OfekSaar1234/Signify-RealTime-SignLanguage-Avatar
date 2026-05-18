"use client"

import { useEffect, useState } from "react"

interface TypewriterProps {
  text: string
  speed?: number
  className?: string
}

export function Typewriter({ text, speed = 40, className }: TypewriterProps) {
  const [displayed, setDisplayed] = useState("")
  const [done, setDone] = useState(false)

  useEffect(() => {
    let i = 0
    setDisplayed("")
    setDone(false)

    const interval = setInterval(() => {
      if (i < text.length) {
        setDisplayed(text.slice(0, i + 1))
        i++
      } else {
        setDone(true)
        clearInterval(interval)
      }
    }, speed)

    return () => clearInterval(interval)
  }, [text, speed])

  return (
    <span className={className}>
      {displayed}
      {!done && <span className="animate-blink">{"_"}</span>}
    </span>
  )
}
