import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Users from './pages/Users'
import Merchants from './pages/Merchants'
import Locations from './pages/Locations'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="navbar">
          <div className="nav-container">
            <h1 className="nav-title">Nerava Admin</h1>
            <div className="nav-links">
              <Link to="/users">Users</Link>
              <Link to="/merchants">Merchants</Link>
              <Link to="/locations">Locations</Link>
            </div>
          </div>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Users />} />
            <Route path="/users" element={<Users />} />
            <Route path="/merchants" element={<Merchants />} />
            <Route path="/locations" element={<Locations />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App

