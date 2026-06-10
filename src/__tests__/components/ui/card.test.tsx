import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardAction,
  CardDescription,
  CardContent,
} from '../../../components/ui/card';

describe('Card (UI)', () => {
  it('renders with data-slot', () => {
    const { container } = render(<Card>Content</Card>);
    expect(container.querySelector('[data-slot="card"]')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<Card className="custom">X</Card>);
    expect(container.firstChild).toHaveClass('custom');
  });
});

describe('CardHeader', () => {
  it('renders with data-slot', () => {
    const { container } = render(<CardHeader>Header</CardHeader>);
    expect(container.querySelector('[data-slot="card-header"]')).toBeInTheDocument();
  });
});

describe('CardTitle', () => {
  it('renders with data-slot', () => {
    const { container } = render(<CardTitle>Title</CardTitle>);
    expect(container.querySelector('[data-slot="card-title"]')).toBeInTheDocument();
  });
});

describe('CardDescription', () => {
  it('renders', () => {
    const { container } = render(<CardDescription>Desc</CardDescription>);
    expect(container.querySelector('[data-slot="card-description"]')).toBeInTheDocument();
  });
});

describe('CardAction', () => {
  it('renders', () => {
    const { container } = render(<CardAction>Act</CardAction>);
    expect(container.querySelector('[data-slot="card-action"]')).toBeInTheDocument();
  });
});

describe('CardContent', () => {
  it('renders with data-slot', () => {
    const { container } = render(<CardContent>Content</CardContent>);
    expect(container.querySelector('[data-slot="card-content"]')).toBeInTheDocument();
  });
});

describe('CardFooter', () => {
  it('renders with data-slot', () => {
    const { container } = render(<CardFooter>Footer</CardFooter>);
    expect(container.querySelector('[data-slot="card-footer"]')).toBeInTheDocument();
  });
});
