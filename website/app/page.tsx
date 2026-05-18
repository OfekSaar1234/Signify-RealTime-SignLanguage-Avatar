import { Navbar } from "@/components/navbar"
import { HeroSection } from "@/components/hero-section"
import { VideoShowcase } from "@/components/video-showcase"
import { HowItWorks } from "@/components/how-it-works"
import { InstallationSection } from "@/components/installation-section"
import { DataPreview } from "@/components/data-preview"
import { Footer } from "@/components/footer"
import { SignAvatar } from "@/components/sign-avatar"

export default function Page() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main>
        <HeroSection />
        <VideoShowcase />
        <HowItWorks />
        <InstallationSection />
        <DataPreview />
      </main>
      <Footer />
      <SignAvatar />
    </div>
  )
}
