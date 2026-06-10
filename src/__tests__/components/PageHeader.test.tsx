import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import PageHeader from '../../components/PageHeader';

describe('PageHeader', () => {
  it('renders title', () => {
    render(<PageHeader title="My Title" />);
    expect(screen.getByText('My Title')).toBeInTheDocument();
  });

  it('renders subtitle when provided', () => {
    render(<PageHeader title="Title" subtitle="Sub" />);
    expect(screen.getByText('Sub')).toBeInTheDocument();
  });

  it('does not render subtitle when not provided', () => {
    const { container } = render(<PageHeader title="Title" />);
    const paragraphs = container.querySelectorAll('p');
    expect(paragraphs.length).toBe(0);
  });

  it('applies custom className', () => {
    const { container } = render(<PageHeader title="T" className="custom" />);
    expect(container.firstChild).toHaveClass('custom');
  });
});
