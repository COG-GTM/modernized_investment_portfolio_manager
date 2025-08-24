export function focusElement(element: HTMLElement | null, options?: FocusOptions): void {
  if (!element) return;
  
  element.focus(options);
  
  element.scrollIntoView({
    behavior: 'smooth',
    block: 'nearest',
    inline: 'nearest'
  });
}

export function trapFocus(container: HTMLElement): () => void {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  const firstElement = focusableElements[0] as HTMLElement;
  const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

  const handleTabKey = (e: KeyboardEvent) => {
    if (e.key !== 'Tab') return;

    if (e.shiftKey) {
      if (document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      }
    } else {
      if (document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    }
  };

  container.addEventListener('keydown', handleTabKey);
  firstElement?.focus();

  return () => {
    container.removeEventListener('keydown', handleTabKey);
  };
}

export function generateAriaLabel(label: string, shortcut?: string, description?: string): string {
  let ariaLabel = label;
  if (shortcut) ariaLabel += ` - Press ${shortcut}`;
  if (description) ariaLabel += ` - ${description}`;
  return ariaLabel;
}
