import { Route, Routes } from 'react-router-dom'
import Home from './pages/Home'
import Report from './pages/Report'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/report/:id" element={<Report />} />
    </Routes>
  )
}
