import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
} from '../../../components/ui/table';

describe('Table components', () => {
  it('renders Table with data-slot', () => {
    const { container } = render(
      <Table>
        <tbody><tr><td>cell</td></tr></tbody>
      </Table>
    );
    expect(container.querySelector('[data-slot="table"]')).toBeInTheDocument();
    expect(container.querySelector('[data-slot="table-container"]')).toBeInTheDocument();
  });

  it('renders TableHeader', () => {
    const { container } = render(
      <table><TableHeader><tr><th>H</th></tr></TableHeader></table>
    );
    expect(container.querySelector('[data-slot="table-header"]')).toBeInTheDocument();
  });

  it('renders TableBody', () => {
    const { container } = render(
      <table><TableBody><tr><td>B</td></tr></TableBody></table>
    );
    expect(container.querySelector('[data-slot="table-body"]')).toBeInTheDocument();
  });

  it('renders TableFooter', () => {
    const { container } = render(
      <table><TableFooter><tr><td>F</td></tr></TableFooter></table>
    );
    expect(container.querySelector('[data-slot="table-footer"]')).toBeInTheDocument();
  });

  it('renders TableRow', () => {
    const { container } = render(
      <table><tbody><TableRow><td>R</td></TableRow></tbody></table>
    );
    expect(container.querySelector('[data-slot="table-row"]')).toBeInTheDocument();
  });

  it('renders TableHead', () => {
    const { container } = render(
      <table><thead><tr><TableHead>TH</TableHead></tr></thead></table>
    );
    expect(container.querySelector('[data-slot="table-head"]')).toBeInTheDocument();
  });

  it('renders TableCell', () => {
    const { container } = render(
      <table><tbody><tr><TableCell>TD</TableCell></tr></tbody></table>
    );
    expect(container.querySelector('[data-slot="table-cell"]')).toBeInTheDocument();
  });

  it('renders TableCaption', () => {
    const { container } = render(
      <table><TableCaption>Caption</TableCaption></table>
    );
    expect(container.querySelector('[data-slot="table-caption"]')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <Table className="custom">
        <tbody><tr><td>cell</td></tr></tbody>
      </Table>
    );
    expect(container.querySelector('[data-slot="table"]')).toHaveClass('custom');
  });
});
