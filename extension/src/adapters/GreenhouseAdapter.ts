import { BaseAdapter, DetectedField, ReviewSummary } from './BaseAdapter';

export class GreenhouseAdapter implements BaseAdapter {
  providerName = 'Greenhouse';
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
    return window.location.hostname.includes('boards.greenhouse.io') || 
           document.querySelector('form[action*="greenhouse.io"]') !== null;
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

      // Greenhouse usually uses a container div with class 'field' and a label
      const fieldContainer = element.closest('.field');
      if (fieldContainer) {
        const labelEl = fieldContainer.querySelector('label');
        if (labelEl) {
          label = labelEl.textContent?.trim() || '';
          // Remove required asterisk and sub-text
          label = label.split('\n')[0].replace('*', '').trim();
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
        required: element.required || (fieldContainer && fieldContainer.querySelector('.asterisk') !== null) || false,
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
    
    // Dispatch event to trigger frontend frameworks if any
    element.dispatchEvent(new Event('change', { bubbles: true }));
    element.dispatchEvent(new Event('input', { bubbles: true }));
  }

  getReviewSummary(): ReviewSummary {
    return { safeFill: 0, reviewRequired: 0, blocked: 0 };
  }

  isBrowserExecutionSupported(): boolean {
    // We only support execution if we can clearly identify the submit button 
    // and no CAPTCHA is present. Greenhouse sometimes uses reCAPTCHA.
    const hasCaptcha = document.querySelector('.g-recaptcha, iframe[src*="recaptcha"]') !== null;
    const submitBtn = document.querySelector('#submit_app, input[type="submit"][value*="Submit"]');
    return !hasCaptcha && submitBtn !== null;
  }

  executeFinalSubmit(): boolean {
    if (!this.isBrowserExecutionSupported()) return false;
    const submitBtn = document.querySelector('#submit_app, input[type="submit"][value*="Submit"]') as HTMLElement;
    if (submitBtn) {
      submitBtn.click();
      return true;
    }
    return false;
  }
}
