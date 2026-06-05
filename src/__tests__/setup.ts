import '@testing-library/jest-dom';
import { vi } from 'vitest';
import React from 'react';

// Mock @radix-ui/react-slot which requires React 18 jsx-runtime
vi.mock('@radix-ui/react-slot', () => ({
  Slot: React.forwardRef(({ children, ...props }: any, ref: any) => {
    if (React.isValidElement(children)) {
      return React.cloneElement(children, { ...props, ref });
    }
    return React.createElement('span', { ...props, ref }, children);
  }),
}));
