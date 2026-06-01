# React 16 → React 19 Migration Plan

## Overview

Migration from React 16.14.0 to React 19.x, including React Router v5 → v6 and TypeScript type updates.

## Phase 1: Dependency Updates (Sequential — must complete before Phase 2)

### Step 1: Update `package.json` and install dependencies

- **File:** `package.json`
- **Changes:**
  - Update `"react": "^16.14.0"` → `"react": "^19.0.0"`
  - Update `"react-dom": "^16.14.0"` → `"react-dom": "^19.0.0"`
  - Update `"react-router-dom": "^5.3.4"` → `"react-router-dom": "^6.28.0"`
  - Remove `"@types/react-router-dom": "^5.3.3"` from dependencies
  - Remove `"@types/react": "^16.14.0"` from devDependencies
  - Remove `"@types/react-dom": "^16.9.0"` from devDependencies
  - Update `"lodash": "4.17.15"` → `"lodash": "^4.17.21"`
- Run `npm install`

## Phase 2: Code Changes (Parallel — all 5 file changes can be done simultaneously in separate Devin sessions)

> **Note:** Each step below is independent and can be assigned to a separate Devin session for parallel execution.

### Step 2A: Update entry point — `src/main.tsx`

- **File:** `src/main.tsx`
- Replace `ReactDOM.render()` with `createRoot()` API
- Replace entire file contents with:

```tsx
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <App />
)
```

### Step 2B: Migrate React Router in `src/App.tsx`

- **File:** `src/App.tsx`
- Replace import: `Switch, Route` from `react-router-dom` → `Routes, Route`
- Replace `<Switch>` with `<Routes>`
- Replace `<Route exact path={...} component={Component} />` with `<Route path={...} element={<Component />} />`
- Remove `exact` prop (v6 matches exactly by default)

### Step 2C: Migrate `src/hooks/useGlobalNavigation.ts`

- **File:** `src/hooks/useGlobalNavigation.ts`
- Replace import: `useHistory` → `useNavigate`
- Replace `const history = useHistory()` → `const navigate = useNavigate()`
- Replace all `history.push(...)` calls → `navigate(...)`
- Update useEffect dependency array: `history` → `navigate`

### Step 2D: Migrate `src/pages/MainMenu.tsx`

- **File:** `src/pages/MainMenu.tsx`
- Replace import: `useHistory` from `react-router-dom` → `useNavigate`
- Replace `const history = useHistory()` → `const navigate = useNavigate()`
- Replace `history.push(...)` → `navigate(...)`

### Step 2E: Migrate `src/pages/TransactionHistory.tsx`

- **File:** `src/pages/TransactionHistory.tsx`
- Replace import: `Link, useLocation` → `Link, useSearchParams`
- Replace `const location = useLocation()` → `const [searchParams] = useSearchParams()`
- Replace `new URLSearchParams(location.search).get('account')` → `searchParams.get('account')`
- Update useEffect dependency array: `location.search` → `searchParams`

## Phase 3: Verification (Sequential — after all Phase 2 steps complete)

### Step 3: Build and test

- Run `npm run build` (runs `tsc && vite build`) to verify TypeScript compilation
- Run `npm run dev` to start dev server
- Test all three pages: MainMenu, PortfolioInquiry, TransactionHistory
- Test keyboard navigation (arrow keys, Escape, number shortcuts)
- Test portfolio search form submission
- Test navigation from portfolio inquiry to transaction history with `?account=` query param

## Files NOT Requiring Changes

| File | Reason |
|------|--------|
| `src/pages/PortfolioInquiry.tsx` | Uses `Link` which is compatible in v6 |
| `src/components/MenuOption.tsx` | Uses `Link` which is compatible in v6 |
| `src/components/AccountInput.tsx` | No router usage |
| All other component and hook files | No React Router or deprecated API usage |

## Notes

- No class components exist in the codebase, simplifying the migration
- `react-hook-form` v7.62+, `@radix-ui/react-slot` v1.x, `lucide-react`, and `@vitejs/plugin-react` v5 are all compatible with React 19
- `lodash` update from 4.17.15 to 4.17.21 fixes known prototype pollution CVEs
