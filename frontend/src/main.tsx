import { MantineProvider } from '@mantine/core'
import '@mantine/core/styles.css'  // <-- Critical, without this nothing looks right
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <MantineProvider>
      <App />
    </MantineProvider>
  </StrictMode>,
)
