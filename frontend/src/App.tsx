import { Routes, Route } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import MainMenu from './pages/MainMenu';
import PortfolioView from './pages/PortfolioView';
import TransactionHistory from './pages/TransactionHistory';

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainMenu />
            </ProtectedRoute>
          }
        />
        <Route
          path="/portfolios/:id"
          element={
            <ProtectedRoute>
              <PortfolioView />
            </ProtectedRoute>
          }
        />
        <Route
          path="/portfolios/:id/history"
          element={
            <ProtectedRoute>
              <TransactionHistory />
            </ProtectedRoute>
          }
        />
      </Routes>
    </ErrorBoundary>
  );
}
