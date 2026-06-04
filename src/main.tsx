import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { I18nProvider } from './i18n/I18nContext'
import './index.css'

const removeTraeLinks = () => {
  const selectors = [
    '#trae-badge-plugin',
    '.trae-badge',
    'a[href*="trae.ai"]',
    'iframe[src*="trae.ai"]',
    'script[src*="trae.ai"]',
    'link[href*="trae.ai"]',
  ]
  document.querySelectorAll(selectors.join(',')).forEach((node) => node.remove())
}

removeTraeLinks()

let scheduled = false
const observer = new MutationObserver(() => {
  if (scheduled) return
  scheduled = true
  requestAnimationFrame(() => {
    scheduled = false
    removeTraeLinks()
  })
})
observer.observe(document.documentElement, { childList: true, subtree: true })

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <I18nProvider>
      <App />
    </I18nProvider>
  </StrictMode>,
)
