import { Route, Routes } from 'react-router-dom'
import Compare from './pages/Compare'
import Home from './pages/Home'
import Report from './pages/Report'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/report/:id" element={<Report />} />
      <Route path="/compare" element={<Compare />} />
    </Routes>
  )
}
