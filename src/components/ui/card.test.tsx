import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardAction,
  CardContent,
  CardFooter,
} from './card';

describe('ui/Card components', () => {
  it('renders Card', () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('Card applies className', () => {
    render(<Card className="my-card">Content</Card>);
    expect(document.querySelector('[data-slot="card"]')).toHaveClass('my-card');
  });

  it('renders CardHeader', () => {
    render(<Card><CardHeader className="my-header">Header</CardHeader></Card>);
    expect(screen.getByText('Header')).toBeInTheDocument();
    expect(document.querySelector('[data-slot="card-header"]')).toHaveClass('my-header');
  });

  it('renders CardTitle', () => {
    render(<Card><CardTitle className="my-title">Title</CardTitle></Card>);
    expect(screen.getByText('Title')).toBeInTheDocument();
    expect(document.querySelector('[data-slot="card-title"]')).toHaveClass('my-title');
  });

  it('renders CardDescription', () => {
    render(<Card><CardDescription className="my-desc">Desc</CardDescription></Card>);
    expect(screen.getByText('Desc')).toBeInTheDocument();
    expect(document.querySelector('[data-slot="card-description"]')).toHaveClass('my-desc');
  });

  it('renders CardAction', () => {
    render(<Card><CardAction className="my-action">Action</CardAction></Card>);
    expect(screen.getByText('Action')).toBeInTheDocument();
    expect(document.querySelector('[data-slot="card-action"]')).toHaveClass('my-action');
  });

  it('renders CardContent', () => {
    render(<Card><CardContent className="my-content">Content</CardContent></Card>);
    expect(screen.getByText('Content')).toBeInTheDocument();
    expect(document.querySelector('[data-slot="card-content"]')).toHaveClass('my-content');
  });

  it('renders CardFooter', () => {
    render(<Card><CardFooter className="my-footer">Footer</CardFooter></Card>);
    expect(screen.getByText('Footer')).toBeInTheDocument();
    expect(document.querySelector('[data-slot="card-footer"]')).toHaveClass('my-footer');
  });
});
