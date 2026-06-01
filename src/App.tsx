import { BrowserRouter as Router, Switch, Route } from 'react-router-dom';
import { MainMenu, PortfolioInquiry, TransactionHistory, TransactionSubmit, TransactionStatusPage } from './pages';
import { ROUTES } from './types/routes';
import { useGlobalNavigation } from './hooks/useGlobalNavigation';

function AppContent() {
  useGlobalNavigation();

  return (
    <Switch>
      <Route exact path={ROUTES.MAIN_MENU} component={MainMenu} />
      <Route path={ROUTES.PORTFOLIO_INQUIRY} component={PortfolioInquiry} />
      <Route path={ROUTES.TRANSACTION_HISTORY} component={TransactionHistory} />
      <Route path={ROUTES.TRANSACTION_SUBMIT} component={TransactionSubmit} />
      <Route path={ROUTES.TRANSACTION_STATUS} component={TransactionStatusPage} />
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
