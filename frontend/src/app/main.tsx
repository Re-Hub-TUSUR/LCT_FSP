import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './app'
import { setupHttp } from './providers/setup-http'
import './styles/tokens.css'
import './styles/global.css'

setupHttp()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
