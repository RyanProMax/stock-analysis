import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// 固定暗黑模式
document.documentElement.classList.add('dark')

createRoot(document.getElementById('root')!).render(<App />)
