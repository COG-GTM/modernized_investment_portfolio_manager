import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import PageHeader from './PageHeader';

describe('PageHeader', () => {
  it('renders title', () => {
    render(<PageHeader title="My Title" />);
    expect(screen.getByText('My Title')).toBeInTheDocument();
  });

  it('renders subtitle when provided', () => {
    render(<PageHeader title="Title" subtitle="My Subtitle" />);
    expect(screen.getByText('My Subtitle')).toBeInTheDocument();
  });

  it('does not render subtitle when not provided', () => {
    const { container } = render(<PageHeader title="Title" />);
    const paragraphs = container.querySelectorAll('p');
    const subtitleParagraphs = Array.from(paragraphs).filter(
      p => p.textContent !== 'Title'
    );
    expect(subtitleParagraphs.length).toBe(0);
  });

  it('applies custom className', () => {
    const { container } = render(<PageHeader title="Title" className="custom" />);
    expect(container.firstChild).toHaveClass('custom');
  });
});
