"use client"

import { motion } from "framer-motion"
import { Database, Copy, Check } from "lucide-react"
import { useState } from "react"

const ease = [0.22, 1, 0.36, 1] as const

const mockJsonData = `{
  "word": "apple",
  "duration_ms": 850,
  "keyframes": [
    {
      "time": 0,
      "right_hand": {
        "position": { "x": 0.12, "y": 0.45, "z": -0.08 },
        "rotation": { "x": -15, "y": 30, "z": 5 },
        "fingers": {
          "thumb": { "curl": 0.2, "spread": 0.4 },
          "index": { "curl": 0.8, "spread": 0.1 },
          "middle": { "curl": 0.9, "spread": 0.0 },
          "ring": { "curl": 0.9, "spread": 0.0 },
          "pinky": { "curl": 0.85, "spread": 0.1 }
        }
      }
    },
    {
      "time": 425,
      "right_hand": {
        "position": { "x": 0.08, "y": 0.42, "z": -0.10 },
        "rotation": { "x": -20, "y": 25, "z": 10 },
        "fingers": {
          "thumb": { "curl": 0.3, "spread": 0.3 },
          "index": { "curl": 0.7, "spread": 0.15 },
          "middle": { "curl": 0.85, "spread": 0.05 },
          "ring": { "curl": 0.9, "spread": 0.0 },
          "pinky": { "curl": 0.8, "spread": 0.15 }
        }
      }
    }
  ],
  "facial_expression": "neutral",
  "transition_type": "smooth"
}`

export function DataPreview() {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(mockJsonData)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <section id="data" className="w-full px-4 py-32 sm:px-6 lg:px-8 bg-background relative overflow-hidden">
      
      {/* Background glow to match the new theme */}
      <div className="absolute inset-0 bg-primary/5 blur-[100px] pointer-events-none" />

      <div className="mx-auto max-w-4xl relative z-10">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: false, margin: "-100px" }}
          transition={{ duration: 0.6, ease }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Database size={16} />
            Behind the Scenes
          </div>
          <h2 className="text-fluid-2 font-display text-foreground mb-4">
            Powered by Custom <br className="md:hidden" />Animation Data
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Each sign is defined by precise 3D coordinate data, enabling smooth and accurate hand movements
          </p>
        </motion.div>

        {/* Code block */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: false, margin: "-50px" }}
          transition={{ duration: 0.6, delay: 0.2, ease }}
          className="relative rounded-2xl overflow-hidden border border-border shadow-2xl bg-[#0A0A0A]"
        >
          {/* Header (Mac style with glossy background) */}
          <div className="flex items-center justify-between bg-white/5 backdrop-blur-md px-6 py-4 border-b border-white/10">
            <div className="flex items-center gap-4">
              <div className="flex gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500/80 shadow-[0_0_8px_rgba(239,68,68,0.5)]" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/80 shadow-[0_0_8px_rgba(234,179,8,0.5)]" />
                <div className="w-3 h-3 rounded-full bg-green-500/80 shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
              </div>
              <span className="text-sm text-white/60 font-mono tracking-wider">apple.json</span>
            </div>
            <button
              onClick={handleCopy}
              className="flex items-center gap-2 text-sm text-white/60 hover:text-white transition-colors"
            >
              {copied ? (
                <>
                  <Check size={16} className="text-primary" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy size={16} />
                  Copy
                </>
              )}
            </button>
          </div>

          {/* Code content */}
          <div className="code-block p-6 overflow-x-auto">
            <pre className="text-sm font-mono leading-relaxed">
              <code className="text-white/90">
                {mockJsonData.split("\n").map((line, i) => (
                  <div key={i} className="table-row">
                    <span className="table-cell pr-6 text-white/30 select-none text-right w-8">
                      {i + 1}
                    </span>
                    <span className="table-cell">
                      {line.includes('"') && (
                        <span
                          dangerouslySetInnerHTML={{
                            __html: line
                              .replace(/"([^"]+)":/g, '<span class="text-cyan-400">"$1"</span>:')
                              .replace(/: "([^"]+)"/g, ': <span class="text-green-400">"$1"</span>')
                              .replace(/: (-?\d+\.?\d*)/g, ': <span class="text-orange-400">$1</span>')
                          }}
                        />
                      )}
                      {!line.includes('"') && line}
                    </span>
                  </div>
                ))}
              </code>
            </pre>
          </div>
        </motion.div>

        {/* Additional info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: false, margin: "-50px" }}
          transition={{ duration: 0.5, delay: 0.4, ease }}
          className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-6"
        >
          {[
            { label: "Sign Definitions", value: "40K+" },
            { label: "Keyframes per Sign", value: "15-30" },
            { label: "Update Frequency", value: "60 FPS" },
          ].map((stat) => (
            <div
              key={stat.label}
              className="bg-card border border-border rounded-xl p-6 text-center hover:border-primary/50 transition-colors shadow-lg shadow-background/50"
            >
              <div className="text-3xl font-display font-bold text-primary mb-2">{stat.value}</div>
              <div className="text-sm text-muted-foreground">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
