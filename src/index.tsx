import { createRoot } from 'react-dom/client'
import { Main } from './components/layout/Main'
import './index.css'

// 固定暗黑模式
document.documentElement.classList.add('dark')

createRoot(document.getElementById('root')!).render(<Main />)
