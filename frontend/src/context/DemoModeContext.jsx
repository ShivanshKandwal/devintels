import { createContext, useContext, useState, useEffect } from 'react'

const DemoModeContext = createContext()

export function DemoModeProvider({ children }) {
  const [demoMode, setDemoMode] = useState(() => {
    const saved = localStorage.getItem('devintel_demo_mode')
    return saved !== null ? saved === 'true' : false // Defaults to false (Live API active) for real results
  })

  useEffect(() => {
    localStorage.setItem('devintel_demo_mode', String(demoMode))
  }, [demoMode])

  return (
    <DemoModeContext.Provider value={{ demoMode, setDemoMode }}>
      {children}
    </DemoModeContext.Provider>
  )
}

export function useDemoMode() {
  const context = useContext(DemoModeContext)
  if (context === undefined) {
    throw new Error('useDemoMode must be used within a DemoModeProvider')
  }
  return context
}
