import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { MainMenu, PortfolioInquiry, TransactionHistory } from './pages';
import { ROUTES } from './types/routes';

function App() {
  return (
    <Router>
      <Routes>
        <Route path={ROUTES.MAIN_MENU} element={<MainMenu />} />
        <Route path={ROUTES.PORTFOLIO_INQUIRY} element={<PortfolioInquiry />} />
        <Route path={ROUTES.TRANSACTION_HISTORY} element={<TransactionHistory />} />
      </Routes>
    </Router>
  )
}

export default App
