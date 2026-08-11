import { BaseAdapter, DetectedField, ReviewSummary } from './BaseAdapter';

export class GenericAdapter implements BaseAdapter {
  providerName = 'Generic ATS';
  version = '1.0';

  getCapabilities() {
    return {
      formDetection: true,
      fieldExtraction: true,
      safeAutofill: true,
      browserExecution: false,
      multiStep: false
    };
  }

  detect(): boolean {
    return true; // Fallback adapter
  }

  extractForm(): DetectedField[] {
    const fields: DetectedField[] = [];
    const inputs = document.querySelectorAll('input, select, textarea');

    inputs.forEach((el) => {
      const element = el as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;
      if (element.type === 'hidden' || element.type === 'file' || element.type === 'submit') return;
      
      const id = element.id || '';
      const name = element.name || '';
      let label = '';

      if (element.labels && element.labels.length > 0) {
        label = element.labels[0].textContent?.trim() || '';
      } else if (element.getAttribute('aria-label')) {
        label = element.getAttribute('aria-label') || '';
      } else if (element.placeholder) {
        label = element.placeholder;
      }

      const options = element.tagName.toLowerCase() === 'select' 
        ? Array.from((element as HTMLSelectElement).options).map(o => o.text)
        : [];

      fields.push({
        id,
        label,
        name,
        type: element.type,
        options: options.length > 0 ? options : undefined,
        required: element.required,
        value: element.value,
        element
      });
    });

    return fields;
  }

  fillField(element: HTMLElement, value: string): void {
    if (element.tagName.toLowerCase() === 'select') {
      const select = element as HTMLSelectElement;
      const option = Array.from(select.options).find(o => o.text === value);
      if (option) {
        select.value = option.value;
      }
    } else {
      (element as HTMLInputElement).value = value;
    }
    
    element.dispatchEvent(new Event('change', { bubbles: true }));
    element.dispatchEvent(new Event('input', { bubbles: true }));
  }

  getReviewSummary(): ReviewSummary {
    return { safeFill: 0, reviewRequired: 0, blocked: 0 };
  }

  isBrowserExecutionSupported(): boolean {
    return false; // Generic ATS must NEVER automatically submit
  }

  executeFinalSubmit(): boolean {
    return false; // Safely fail closed
  }
}
