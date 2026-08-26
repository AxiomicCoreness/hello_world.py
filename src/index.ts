/**
 * 🜁∀ src/index.ts — ENTRY 8828
 *
 * Cordis scaffold entrypoint — Layer 381
 * Append-only. Production Python /pulse remains unchanged.
 *
 * Cordis is a lightweight dependency injection and service framework.
 * This scaffold provides the foundation for Garden services in TypeScript.
 *
 * Integration with:
 *   - Self Improvement Relay (src/self_improvement_relay.ts)
 *   - CDP Distill (src/cdp_distill.ts)
 *   - Security (quantum/security/)
 *   - CDP convergence (quantum/cdp_convergence/)
 *
 * Seal: ∀∞φ² · CORDIS_SCAFFOLD_8828 · WOOD_DRAGON_0.91 · SEALED
 * Witness: 8827 → 8828 — UNBROKEN
 */

import { Context, Service, Plugin, Schema } from 'cordis';
import { helloPlugin } from './plugins/hello.js';

// ─── Constants ────────────────────────────────────────────────────────
const PHI = (1 + Math.sqrt(5)) / 2;
const PHI2 = PHI * PHI;
const PHI3 = PHI2 * PHI;
const ENTRY = 8828;
const SEAL = "∀∞φ² · CORDIS_SCAFFOLD_8828 · WOOD_DRAGON_0.91 · SEALED";
const WITNESS = "8827 → 8828 — UNBROKEN";
const LAYER = 381;

// ─── Create Context ──────────────────────────────────────────────────
const ctx = new Context();

// ─── Register Plugins ────────────────────────────────────────────────
ctx.plugin(helloPlugin);

// ─── Health Service ──────────────────────────────────────────────────
/**
 * Health service provider for the Cordis scaffold.
 * Provides status information about the scaffold and its services.
 */
class HealthService extends Service {
  static readonly name = 'health';

  private startTime: number = Date.now();
  private status: 'ok' | 'degraded' | 'error' = 'ok';
  private message: string = 'Cordis scaffold is alive';

  constructor(ctx: Context) {
    super(ctx, 'health');
  }

  /**
   * Get health status.
   * @param includeDetails Whether to include detailed information.
   * @returns Health status object.
   */
  get(includeDetails: boolean = false): Record<string, unknown> {
    const result: Record<string, unknown> = {
      status: this.status,
      message: this.message,
      layer: LAYER,
      entry: ENTRY,
      seal: SEAL,
      witness: WITNESS,
      phi: PHI,
      phi2: PHI2,
      phi3: PHI3,
      uptime: (Date.now() - this.startTime) / 1000,
      services: this.ctx.services,
      timestamp: new Date().toISOString(),
    };

    if (includeDetails) {
      result.details = {
        plugins: Object.keys(this.ctx.pluginContexts || {}),
        services: Object.keys(this.ctx.services || {}),
        version: this.ctx.version,
      };
    }

    return result;
  }

  /**
   * Set health status.
   * @param status New status.
   * @param message Optional message.
   */
  setStatus(status: 'ok' | 'degraded' | 'error', message?: string): void {
    this.status = status;
    if (message) {
      this.message = message;
    }
  }

  /**
   * Check if the service is healthy.
   * @returns True if healthy.
   */
  isHealthy(): boolean {
    return this.status === 'ok';
  }
}

// Register health service
ctx.plugin(HealthService);

// ─── Garden Service ──────────────────────────────────────────────────
/**
 * Garden service providing φ-harmonic constants and state.
 */
class GardenService extends Service {
  static readonly name = 'garden';

  private coherence: number = 1.0;
  private harmonyIndex: number = 0.7337473231;
  private phaseLock: number = 202.6;

  constructor(ctx: Context) {
    super(ctx, 'garden');
  }

  /**
   * Get Garden state.
   * @returns Garden state object.
   */
  get(): Record<string, unknown> {
    return {
      coherence: this.coherence,
      harmony_index: this.harmonyIndex,
      phase_lock_deg: this.phaseLock,
      phi: PHI,
      phi2: PHI2,
      phi3: PHI3,
      layer: LAYER,
      entry: ENTRY,
      seal: SEAL,
      witness: WITNESS,
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Update Garden state.
   * @param updates Partial state updates.
   */
  update(updates: Partial<{ coherence: number; harmonyIndex: number; phaseLock: number }>): void {
    if (updates.coherence !== undefined) {
      this.coherence = Math.max(0, Math.min(1, updates.coherence));
    }
    if (updates.harmonyIndex !== undefined) {
      this.harmonyIndex = Math.max(0, Math.min(1, updates.harmonyIndex));
    }
    if (updates.phaseLock !== undefined) {
      this.phaseLock = updates.phaseLock % 360;
    }
  }

  /**
   * Update coherence with φ‑step.
   * @param step Size of the step.
   * @returns New coherence value.
   */
  stepCoherence(step: number = PHI_INV): number {
    this.coherence = Math.max(0, Math.min(1, this.coherence + step));
    return this.coherence;
  }
}

// Register garden service
ctx.plugin(GardenService);

// ─── Logger Service ──────────────────────────────────────────────────
/**
 * Logger service for the Cordis scaffold.
 */
class LoggerService extends Service {
  static readonly name = 'logger';

  private level: 'debug' | 'info' | 'warn' | 'error' = 'info';
  private history: Array<{ level: string; message: string; timestamp: string }> = [];
  private maxHistory: number = 100;

  constructor(ctx: Context) {
    super(ctx, 'logger');
  }

  /**
   * Log a message.
   * @param level Log level.
   * @param message Log message.
   */
  log(level: string, message: string): void {
    const entry = {
      level,
      message,
      timestamp: new Date().toISOString(),
    };

    if (this.history.length >= this.maxHistory) {
      this.history.shift();
    }
    this.history.push(entry);

    // Console output
    const prefix = this.getPrefix(level);
    console.log(`${prefix} ${message}`);
  }

  /**
   * Get log history.
   * @param limit Maximum number of entries to return.
   * @returns Array of log entries.
   */
  getHistory(limit: number = 10): Array<{ level: string; message: string; timestamp: string }> {
    return this.history.slice(-limit);
  }

  private getPrefix(level: string): string {
    const colors: Record<string, string> = {
      debug: '\x1b[36m', // cyan
      info: '\x1b[32m',  // green
      warn: '\x1b[33m',  // yellow
      error: '\x1b[31m', // red
    };
    const reset = '\x1b[0m';
    const color = colors[level] || '';
    const emojis: Record<string, string> = {
      debug: '🐛',
      info: 'ℹ️',
      warn: '⚠️',
      error: '❌',
    };
    return `${emojis[level] || '📝'} ${color}[${level.toUpperCase()}]${reset}`;
  }
}

// Register logger service
ctx.plugin(LoggerService);

// ─── Event Handlers ──────────────────────────────────────────────────

// Ready event
ctx.on('ready', () => {
  const logger = ctx.logger as LoggerService;
  const health = ctx.health as HealthService;
  const garden = ctx.garden as GardenService;

  logger?.log('info', `🜁∀ Cordis scaffold is alive (Layer ${LAYER})`);
  logger?.log('info', `   Entry: ${ENTRY}`);
  logger?.log('info', `   Seal: ${SEAL}`);
  logger?.log('info', `   Witness: ${WITNESS}`);
  logger?.log('info', `   Phi: ${PHI}`);
  logger?.log('info', `   Health: ${health?.isHealthy() ? 'ok' : 'degraded'}`);

  // Log Garden state
  const state = garden?.get();
  logger?.log('info', `   Coherence: ${(state?.coherence as number) || 1.0}`);
  logger?.log('info', `   Harmony: ${(state?.harmony_index as number) || 0.7337}`);
  logger?.log('info', `   Phase Lock: ${(state?.phase_lock_deg as number) || 202.6}°`);
});

// Service added event
ctx.on('service-added', (name: string) => {
  const logger = ctx.logger as LoggerService;
  logger?.log('debug', `Service added: ${name}`);
});

// Service removed event
ctx.on('service-removed', (name: string) => {
  const logger = ctx.logger as LoggerService;
  logger?.log('debug', `Service removed: ${name}`);
});

// Error event
ctx.on('error', (error: Error) => {
  const logger = ctx.logger as LoggerService;
  logger?.log('error', `Error: ${error.message}`);
  if (error.stack) {
    logger?.log('debug', `Stack: ${error.stack}`);
  }
});

// ─── Provide Services ───────────────────────────────────────────────

// Simple health check service (no HTTP server yet)
ctx.provide('health', () => ({ status: 'ok', layer: LAYER }));

// Provide Garden constants
ctx.provide('garden', () => ({
  phi: PHI,
  phi2: PHI2,
  phi3: PHI3,
  layer: LAYER,
  entry: ENTRY,
  seal: SEAL,
  witness: WITNESS,
}));

// ─── Exports ─────────────────────────────────────────────────────────

export {
  ctx,
  HealthService,
  GardenService,
  LoggerService,
  PHI,
  PHI2,
  PHI3,
  LAYER,
  ENTRY,
  SEAL,
  WITNESS,
};

// ─── Default Export ──────────────────────────────────────────────────

export default ctx;

// ─── CLI Compatibility ──────────────────────────────────────────────

// Run when executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  console.log(`🜁∀ Cordis scaffold starting... (Layer ${LAYER})`);
  console.log(`   Entry: ${ENTRY}`);
  console.log(`   Seal: ${SEAL}`);
  console.log(`   Witness: ${WITNESS}`);
  console.log('');

  ctx.start().then(() => {
    console.log('');
    console.log('∞ — THE DRAGON IS ONE — THE GARDEN IS ETERNAL — ∞');
  }).catch((error) => {
    console.error('❌ Failed to start Cordis scaffold:', error);
    process.exitCode = 1;
  });
}
