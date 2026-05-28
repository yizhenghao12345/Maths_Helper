import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Home from '@/pages/Home'
import ProblemInput from '@/pages/ProblemInput'
import Deduction from '@/pages/Deduction'

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/input" element={<ProblemInput />} />
        <Route path="/deduction" element={<Deduction />} />
      </Routes>
    </Router>
  )
}
