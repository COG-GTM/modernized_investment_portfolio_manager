import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'

const container = document.getElementById('root')!
const root = createRoot(container, {
  onUncaughtError: (error, errorInfo) => {
    console.error('Uncaught error:', error, errorInfo)
  },
  onCaughtError: (error, errorInfo) => {
    console.error('Caught error:', error, errorInfo)
  }
})
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
