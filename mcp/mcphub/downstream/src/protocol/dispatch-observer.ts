import type { ThingsProtocolHandler } from "./types.js";

export interface ProtocolDispatchSnapshot {
  readonly sdk: number;
  readonly provider: number;
}

export class ProtocolDispatchObserver {
  private sdkDispatchCount = 0;
  private providerDispatchCount = 0;

  public recordSdkDispatch(): void {
    this.sdkDispatchCount += 1;
  }

  public recordProviderDispatch(): void {
    this.providerDispatchCount += 1;
  }

  public snapshot(): ProtocolDispatchSnapshot {
    return {
      sdk: this.sdkDispatchCount,
      provider: this.providerDispatchCount,
    };
  }
}

const HANDLER_OBSERVERS = new WeakMap<
  ThingsProtocolHandler,
  ProtocolDispatchObserver
>();

export function attachProtocolDispatchObserver(
  handler: ThingsProtocolHandler,
  observer: ProtocolDispatchObserver,
): void {
  HANDLER_OBSERVERS.set(handler, observer);
}

export function protocolDispatchSnapshot(
  handler: ThingsProtocolHandler,
): ProtocolDispatchSnapshot {
  const observer = HANDLER_OBSERVERS.get(handler);
  if (observer === undefined) {
    throw new Error("protocol_dispatch_observer_unavailable");
  }
  return observer.snapshot();
}
