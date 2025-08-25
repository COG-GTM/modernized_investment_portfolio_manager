import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { 
  MainMenu, 
  PortfolioInquiry, 
  TransactionHistory, 
  ReportsAnalytics, 
  SystemAdministration, 
  AuditCompliance, 
  HelpDocumentation 
} from './pages';
import { ROUTES } from './types/routes';
import { useGlobalNavigation } from './hooks/useGlobalNavigation';

function AppContent() {
  useGlobalNavigation();

  return (
    <Routes>
      <Route path={ROUTES.MAIN_MENU} element={<MainMenu />} />
      <Route path={ROUTES.PORTFOLIO_INQUIRY} element={<PortfolioInquiry />} />
      <Route path={ROUTES.TRANSACTION_HISTORY} element={<TransactionHistory />} />
      <Route path={ROUTES.REPORTS_ANALYTICS} element={<ReportsAnalytics />} />
      <Route path={ROUTES.SYSTEM_ADMINISTRATION} element={<SystemAdministration />} />
      <Route path={ROUTES.AUDIT_COMPLIANCE} element={<AuditCompliance />} />
      <Route path={ROUTES.HELP_DOCUMENTATION} element={<HelpDocumentation />} />
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

export default App;
