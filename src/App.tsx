import { BrowserRouter as Router, Switch, Route } from 'react-router-dom';
import { MainMenu, PortfolioInquiry, TransactionHistory } from './pages';
import { ROUTES } from './types/routes';
import { useGlobalNavigation } from './hooks/useGlobalNavigation';
import { ThemeProvider } from './hooks/useTheme';
import ThemeToggle from './components/ThemeToggle';

function AppContent() {
  useGlobalNavigation();

  return (
    <>
      <ThemeToggle />
      <Switch>
        <Route exact path={ROUTES.MAIN_MENU} component={MainMenu} />
        <Route path={ROUTES.PORTFOLIO_INQUIRY} component={PortfolioInquiry} />
        <Route path={ROUTES.TRANSACTION_HISTORY} component={TransactionHistory} />
      </Switch>
    </>
  );
}

function App() {
  return (
    <ThemeProvider>
      <Router>
        <AppContent />
      </Router>
    </ThemeProvider>
  )
}

export default App
