import { useState, useEffect } from 'react'
import { HashRouter, Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import Navbar from './components/Navbar'
import ErrorBoundary from './components/ErrorBoundary'
import Landing from './pages/Landing'
import Landscape from './pages/Landscape'
import Analyzer from './pages/Analyzer'
import Forecast from './pages/Forecast'
import Tribe from './pages/Tribe'
import { DemoModeProvider } from './context/DemoModeContext'

const pageVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } },
  exit: { opacity: 0, y: -12, transition: { duration: 0.25 } },
}

function AnimatedRoutes() {
  const location = useLocation()

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route
          path="/"
          element={
            <motion.div {...pageVariants}>
              <Landing />
            </motion.div>
          }
        />
        <Route
          path="/landscape"
          element={
            <motion.div {...pageVariants}>
              <Landscape />
            </motion.div>
          }
        />
        <Route
          path="/analyzer"
          element={
            <motion.div {...pageVariants}>
              <Analyzer />
            </motion.div>
          }
        />
        <Route
          path="/forecast"
          element={
            <motion.div {...pageVariants}>
              <Forecast />
            </motion.div>
          }
        />
        <Route
          path="/tribe"
          element={
            <motion.div {...pageVariants}>
              <Tribe />
            </motion.div>
          }
        />
      </Routes>
    </AnimatePresence>
  )
}

function LayoutWrapper() {
  const location = useLocation()
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })

  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePos({ x: e.clientX, y: e.clientY })
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  // Spotlight color based on route
  const getGlowColor = () => {
    switch (location.pathname) {
      case '/landscape':
        return 'radial-gradient(circle, rgba(14, 165, 233, 0.22) 0%, rgba(14, 165, 233, 0) 70%)'
      case '/analyzer':
        return 'radial-gradient(circle, rgba(236, 72, 153, 0.22) 0%, rgba(236, 72, 153, 0) 70%)'
      case '/forecast':
        return 'radial-gradient(circle, rgba(245, 158, 11, 0.22) 0%, rgba(245, 158, 11, 0) 70%)'
      case '/tribe':
        return 'radial-gradient(circle, rgba(168, 85, 247, 0.22) 0%, rgba(168, 85, 247, 0) 70%)'
      default:
        return 'radial-gradient(circle, rgba(99, 102, 241, 0.22) 0%, rgba(99, 102, 241, 0) 70%)'
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden selection:bg-purple-light/20 selection:text-text-primary text-text-secondary pb-12">
      {/* Spotlight cursor glow */}
      <div
        className="cursor-glow"
        style={{
          left: mousePos.x,
          top: mousePos.y,
          background: getGlowColor(),
        }}
      />

      {/* Background patterns */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute inset-0 bg-blueprint" />
        <div className="absolute inset-0 bg-grid-lines" />
        <div className="absolute inset-0 bg-topo" />
        <div className="absolute inset-0 bg-crosshatch" />

        {/* Saturated animated blobs */}
        <div className="absolute top-[-10%] left-[-5%] w-[600px] h-[600px] blob blob-purple opacity-45" />
        <div className="absolute bottom-[10%] right-[-10%] w-[700px] h-[700px] blob blob-indigo opacity-40" />
        <div className="absolute top-[35%] left-[25%] w-[600px] h-[600px] blob blob-pink opacity-35" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[650px] h-[650px] blob blob-cyan opacity-35" />
      </div>

      {/* Content wrapper */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        <Navbar />
        <ErrorBoundary>
          <AnimatedRoutes />
        </ErrorBoundary>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <DemoModeProvider>
      <HashRouter>
        <LayoutWrapper />
      </HashRouter>
    </DemoModeProvider>
  )
}
