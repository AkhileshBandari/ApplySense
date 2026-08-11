import { BaseAdapter, DetectedField, ReviewSummary, AdapterCapabilities } from './BaseAdapter';

export class SmartRecruitersAdapter implements BaseAdapter {
  providerName = 'SmartRecruiters';
  version = '1.0';

  getCapabilities(): AdapterCapabilities {
    return {
      formDetection: true,
      fieldExtraction: true,
      safeAutofill: true,
      browserExecution: false,
      multiStep: false
    };
  }

  detect(): boolean {
    return window.location.hostname.includes('smartrecruiters.com') ||
           document.querySelector('script[src*="smartrecruiters"]') !== null;
  }

  extractForm(): DetectedField[] {
    const fields: DetectedField[] = [];
    const inputs = document.querySelectorAll('input, select, textarea');

    inputs.forEach((el) => {
      const element = el as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;
      if (element.type === 'hidden' || element.type === 'file') return;

      const id = element.id || '';
      const name = element.name || '';
      
      let label = '';
      const formGroup = element.closest('.form-group');
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
        required: element.hasAttribute('required') || (formGroup?.querySelector('.required-asterisk') !== null) || false,
        value: element.value,
        element
      });
    });

    return fields;
  }

  fillField(element: HTMLElement, value: string): void {
    if (element.tagName.toLowerCase() === 'select') {
      const select = element as HTMLSelectElement;
      const option = Array.from(select.options).find(o => o.text.includes(value));
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
    return false;
  }

  executeFinalSubmit(): boolean {
    return false;
  }
}
