import { BaseAdapter } from './adapters/BaseAdapter';
import { GreenhouseAdapter } from './adapters/GreenhouseAdapter';
import { LeverAdapter } from './adapters/LeverAdapter';
import { AshbyAdapter } from './adapters/AshbyAdapter';
import { GenericAdapter } from './adapters/GenericAdapter';

export class ApplicationPageDetector {
  private adapters: BaseAdapter[] = [
    new GreenhouseAdapter(),
    new LeverAdapter(),
    new AshbyAdapter()
  ];

  detectAdapter(): BaseAdapter {
    for (const adapter of this.adapters) {
      if (adapter.detect()) {
        return adapter;
      }
    }
    // Fallback
    return new GenericAdapter();
  }
}
