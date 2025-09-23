import { useEffect } from 'react';
import { useHistory, useLocation } from 'react-router-dom';
import { ROUTES } from '../types/routes';

export function useGlobalNavigation() {
  const history = useHistory();
  const location = useLocation();

  useEffect(() => {
    const handleGlobalKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        if (location.pathname === ROUTES.MAIN_MENU) {
          return;
        }

        const activeElement = document.activeElement;
        if (activeElement && (
          activeElement.tagName === 'INPUT' ||
          activeElement.tagName === 'TEXTAREA' ||
          activeElement.getAttribute('contenteditable') === 'true'
        )) {
          return;
        }

        const modalElement = document.querySelector('[aria-modal="true"]');
        if (modalElement) {
          return;
        }

        event.preventDefault();
        history.push(ROUTES.MAIN_MENU);
      }
    };

    document.addEventListener('keydown', handleGlobalKeyDown);

    return () => {
      document.removeEventListener('keydown', handleGlobalKeyDown);
    };
  }, [history, location.pathname]);
}
