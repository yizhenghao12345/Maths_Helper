import { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'

const Home = lazy(() => import('@/pages/Home'))
const ProblemInput = lazy(() => import('@/pages/ProblemInput'))
const Deduction = lazy(() => import('@/pages/Deduction'))
const Console = lazy(() => import('@/pages/Console'))

export default function App() {
  return (
    <Router>
      <Suspense>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/input" element={<ProblemInput />} />
          <Route path="/deduction" element={<Deduction />} />
          <Route path="/console" element={<Console />} />
        </Routes>
      </Suspense>
    </Router>
  )
}
