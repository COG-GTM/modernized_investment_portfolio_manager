import { BrowserRouter as Router, Switch, Route } from 'react-router-dom';
import { PortfolioInquiry, TransactionHistory } from './pages';
import Menu from './components/Menu';
import { ROUTES } from './types/routes';
import { useGlobalNavigation } from './hooks/useGlobalNavigation';

function AppContent() {
  useGlobalNavigation();

  return (
    <Switch>
      <Route exact path={ROUTES.MAIN_MENU} component={Menu} />
      <Route path={ROUTES.PORTFOLIO_INQUIRY} component={PortfolioInquiry} />
      <Route path={ROUTES.TRANSACTION_HISTORY} component={TransactionHistory} />
    </Switch>
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
