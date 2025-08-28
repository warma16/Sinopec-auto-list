type EventCallback<T = any> = (data: T) => void;
type ListenerRecord = {
  callback: EventCallback;
  handler: EventListener;
};

class EvBox {
  private event_token: string;
  private eventsNames: string[] = [];
  private eventMap: Map<string, ListenerRecord[]> = new Map();

  constructor() {
    this.event_token = `-EVBOX?t=${Date.now()}&id=${this.gn_box_id()}`;
  }

  /** Emit a custom event */
  emit<T = unknown>(name: string, data?: T): void {
    logging('emit event');
    if (!this.eventsNames.includes(name)) {
      this.eventsNames.push(name);
    }
    
    const fullEventName = name + this.event_token;
    window.dispatchEvent(new CustomEvent(fullEventName, { detail: data }));
    logging(`emit event ${name} done`);
  }

  /** Register an event listener */
  on<T = unknown>(name: string, cb: EventCallback<T>): void {
    logging(`register event ${name}`);
    
    const fullEventName = name + this.event_token;
    if (!this.eventsNames.includes(name)) {
      this.eventsNames.push(name);
    }
    
    const handler = (event: Event) => {
      const customEvent = event as CustomEvent<T>;
      logging(`event ${name} received`);
      logging(customEvent.detail);
      cb(customEvent.detail);
    };
    
    window.addEventListener(fullEventName, handler);
    
    // Store listener for potential removal
    const record: ListenerRecord = { callback: cb, handler };
    const records = this.eventMap.get(fullEventName) || [];
    records.push(record);
    this.eventMap.set(fullEventName, records);
    
    logging(`register event ${name} done`);
  }

  /** Remove an event listener */
  off(evname: string, cb: EventCallback): void {
    const fullEventName = evname + this.event_token;
    const records = this.eventMap.get(fullEventName);
    
    if (!records) return;
    
    const remaining = records.filter(record => {
      if (record.callback === cb) {
        window.removeEventListener(fullEventName, record.handler);
        return false;
      }
      return true;
    });
    
    if (remaining.length === 0) {
      this.eventMap.delete(fullEventName);
    } else {
      this.eventMap.set(fullEventName, remaining);
    }
  }

  /** Remove all listeners for an event */
  clear(evname: string): void {
    const fullEventName = evname + this.event_token;
    const records = this.eventMap.get(fullEventName);
    
    if (!records) return;
    
    records.forEach(record => {
      window.removeEventListener(fullEventName, record.handler);
    });
    
    this.eventMap.delete(fullEventName);
  }

  /** Clean up all listeners */
  destroy(): void {
    this.eventMap.forEach((records, fullEventName) => {
      records.forEach(record => {
        window.removeEventListener(fullEventName, record.handler);
      });
    });
    this.eventMap.clear();
  }

  /** Generate unique box ID */
  private gn_box_id(): string {
    return `${Date.now()}-${Math.random().toString(36).slice(2, 12)}`;
  }
}

/** Log utility function */
function logging(anyone: unknown): void {
  console.log(`[evbox]: ${String(anyone)}`);
}

export default EvBox