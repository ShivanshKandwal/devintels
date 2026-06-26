import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import Navbar from './components/Navbar'
import ErrorBoundary from './components/ErrorBoundary'
import Landing from './pages/Landing'
import Landscape from './pages/Landscape'
import Analyzer from './pages/Analyzer'
import Forecast from './pages/Forecast'
import Tribe from './pages/Tribe'

const pageVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.35, ease: 'easeOut' } },
  exit: { opacity: 0, y: -12, transition: { duration: 0.2 } },
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

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-dark-bg text-text-primary">
        <Navbar />
        <ErrorBoundary>
          <AnimatedRoutes />
        </ErrorBoundary>
      </div>
    </BrowserRouter>
  )
}
