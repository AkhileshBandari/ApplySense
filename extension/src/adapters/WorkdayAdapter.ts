import { BaseAdapter, DetectedField, ReviewSummary, AdapterCapabilities } from './BaseAdapter';

export class WorkdayAdapter implements BaseAdapter {
  providerName = 'Workday';
  version = '1.0';

  getCapabilities(): AdapterCapabilities {
    return {
      formDetection: true,
      fieldExtraction: true,
      safeAutofill: true,
      browserExecution: false, // Too complex/captcha heavy for now
      multiStep: true
    };
  }

  detect(): boolean {
    return window.location.hostname.includes('myworkdayjobs.com') ||
           document.querySelector('div[data-automation-id="workday-application"]') !== null;
  }

  extractForm(): DetectedField[] {
    const fields: DetectedField[] = [];
    // Workday uses data-automation-id heavily
    const inputs = document.querySelectorAll('input, select, textarea');

    inputs.forEach((el) => {
      const element = el as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;
      if (element.type === 'hidden' || element.type === 'file') return;

      const id = element.id || '';
      const name = element.name || '';
      
      let label = '';
      const formGroup = element.closest('div[data-automation-id="formField"]');
      if (formGroup) {
        const labelEl = formGroup.querySelector('label');
        if (labelEl) {
          label = labelEl.textContent?.trim() || '';
          label = label.replace('*', '').trim();
        }
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
        required: element.getAttribute('aria-required') === 'true' || false,
        value: element.value,
        element
      });
    });

    return fields;
  }

  fillField(element: HTMLElement, value: string): void {
    if (element.tagName.toLowerCase() === 'select') {
      // Workday has custom dropdowns but sometimes falls back to select
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
    element.dispatchEvent(new Event('blur', { bubbles: true })); // Workday triggers validation on blur
  }

  getReviewSummary(): ReviewSummary {
    return { safeFill: 0, reviewRequired: 0, blocked: 0 };
  }

  isBrowserExecutionSupported(): boolean {
    return false;
  }

  executeFinalSubmit(): boolean {
    return false;
  }
}
