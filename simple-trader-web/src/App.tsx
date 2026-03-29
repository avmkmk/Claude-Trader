import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Layout from './components/layout/Layout'
import Auth from './pages/Auth'
import Dashboard from './pages/Dashboard'
import Holdings from './pages/Holdings'
import Orders from './pages/Orders'
import Strategies from './pages/Strategies'
import Watchlist from './pages/Watchlist'
import Signals from './pages/Signals'
import News from './pages/News'
import AIChat from './pages/AIChat'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/auth" replace />
}

function App() {
  return (
    <Routes>
      <Route path="/auth" element={<Auth />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="holdings" element={<Holdings />} />
        <Route path="orders" element={<Orders />} />
        <Route path="strategies" element={<Strategies />} />
        <Route path="watchlist" element={<Watchlist />} />
        <Route path="signals" element={<Signals />} />
        <Route path="news" element={<News />} />
        <Route path="ai" element={<AIChat />} />
      </Route>
    </Routes>
  )
}

export default App
