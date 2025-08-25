import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { MainMenu, PortfolioInquiry, TransactionHistory } from './pages';
import { ROUTES } from './types/routes';
import { useGlobalNavigation } from './hooks/useGlobalNavigation';

function AppContent() {
  useGlobalNavigation();

  return (
    <Routes>
      <Route path={ROUTES.MAIN_MENU} element={<MainMenu />} />
      <Route path={ROUTES.PORTFOLIO_INQUIRY} element={<PortfolioInquiry />} />
      <Route path={ROUTES.TRANSACTION_HISTORY} element={<TransactionHistory />} />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  )
}

export default App
