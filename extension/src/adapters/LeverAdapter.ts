import { BaseAdapter, DetectedField, ReviewSummary } from './BaseAdapter';

export class LeverAdapter implements BaseAdapter {
  providerName = 'Lever';
  version = '1.0';

  getCapabilities() {
    return {
      formDetection: true,
      fieldExtraction: true,
      safeAutofill: true,
      browserExecution: true,
      multiStep: false
    };
  }

  detect(): boolean {
    return window.location.hostname.includes('jobs.lever.co') || 
           document.querySelector('form[action*="lever.co"]') !== null;
  }

  extractForm(): DetectedField[] {
    const fields: DetectedField[] = [];
    const inputs = document.querySelectorAll('.application-field input, .application-field select, .application-field textarea');

    inputs.forEach((el) => {
      const element = el as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;
      if (element.type === 'hidden' || element.type === 'file') return;
      
      const id = element.id || '';
      const name = element.name || '';
      let label = '';

      const fieldContainer = element.closest('.application-field');
      if (fieldContainer) {
        const labelEl = fieldContainer.querySelector('.application-label');
        if (labelEl) {
          label = labelEl.textContent?.replace('*', '').trim() || '';
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
        required: element.required || (fieldContainer && fieldContainer.querySelector('.required') !== null) || false,
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
    const hasCaptcha = document.querySelector('.h-captcha, .g-recaptcha, iframe[src*="recaptcha"], iframe[src*="hcaptcha"]') !== null;
    const submitBtn = document.querySelector('button.template-btn-submit, button[type="submit"]');
    return !hasCaptcha && submitBtn !== null;
  }

  executeFinalSubmit(): boolean {
    if (!this.isBrowserExecutionSupported()) return false;
    const submitBtn = document.querySelector('button.template-btn-submit, button[type="submit"]') as HTMLElement;
    if (submitBtn) {
      submitBtn.click();
      return true;
    }
    return false;
  }
}
