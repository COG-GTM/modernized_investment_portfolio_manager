import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import SampleComponent from './SampleComponent';

describe('SampleComponent', () => {
  it('renders portfolio dashboard title', () => {
    render(<SampleComponent />);
    expect(screen.getByText('Portfolio Dashboard')).toBeInTheDocument();
  });

  it('renders description', () => {
    render(<SampleComponent />);
    expect(
      screen.getByText('Manage your investment portfolio with modern tools')
    ).toBeInTheDocument();
  });

  it('renders Create Portfolio button', () => {
    render(<SampleComponent />);
    expect(screen.getByText('Create Portfolio')).toBeInTheDocument();
  });

  it('renders View Reports button', () => {
    render(<SampleComponent />);
    expect(screen.getByText('View Reports')).toBeInTheDocument();
  });

  it('renders portfolio name input', () => {
    render(<SampleComponent />);
    expect(screen.getByPlaceholderText('Enter portfolio name')).toBeInTheDocument();
  });

  it('renders Total Value card', () => {
    render(<SampleComponent />);
    expect(screen.getByText('Total Value')).toBeInTheDocument();
    expect(screen.getByText('$125,430')).toBeInTheDocument();
  });

  it('renders Daily Change card', () => {
    render(<SampleComponent />);
    expect(screen.getByText('Daily Change')).toBeInTheDocument();
    expect(screen.getByText('+2.4%')).toBeInTheDocument();
  });

  it('renders Holdings card', () => {
    render(<SampleComponent />);
    expect(screen.getByText('Holdings')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
  });

  it('renders sample description alert', () => {
    render(<SampleComponent />);
    expect(screen.getByText(/sample component demonstrating/)).toBeInTheDocument();
  });
});
