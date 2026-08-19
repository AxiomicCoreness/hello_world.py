/**
 * 🜁∀ src/self_improvement_relay.ts
 * Self-improvement relay for the Sovereign Garden lattice.
 *
 * Relays graded outcomes (pass / fail / soft) toward:
 *   - Port-380 MCP  POST /pulse  (optional)
 *   - Python harness suite hints (offline echo)
 *   - Local lesson buffer (in-memory, no disk required)
 *
 * Designed to fix the missing-module error: this path is now on main.
 * Runtime: Node 18+ (global fetch) or any fetch-capable host.
 *
 * Seal: ∀∞φ² · SELF_IMPROVEMENT_RELAY · WOOD_DRAGON_0.91 · SEALED
 */

export type Grade = "pass" | "fail" | "soft";

export interface Lesson {
  id: string;
  ts: number;
  grade: Grade;
  source: string;
  message: string;
  patchHint?: string;
  meta?: Record<string, unknown>;
}

export interface RelayConfig {
  /** Base URL for Port-380 / MCP surface, e.g. http://127.0.0.1:8080 */
  mcpBaseUrl?: string;
  /** X-Garden-Secret header value when calling /pulse */
  gardenSecret?: string;
  /** Prefer offline only (no network) */
  offline?: boolean;
  /** Max lessons retained in memory */
  maxLessons?: number;
  /** Phase lock degrees (Garden invariant) */
  phaseLockDeg?: number;
}

export interface RelayResult {
  ok: boolean;
  mode: "offline" | "pulse" | "error";
  lesson: Lesson;
  response?: unknown;
  error?: string;
}

const PHI = (1 + Math.sqrt(5)) / 2;
const DEFAULT_PHASE = 202.6;

function newId(): string {
  return `sir_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
}

/**
 * SelfImprovementRelay — buffers lessons and optionally pulses the Garden gate.
 */
export class SelfImprovementRelay {
  private lessons: Lesson[] = [];
  private readonly cfg: Required<
    Pick<RelayConfig, "offline" | "maxLessons" | "phaseLockDeg">
  > &
    RelayConfig;

  constructor(config: RelayConfig = {}) {
    this.cfg = {
      offline: config.offline ?? !config.mcpBaseUrl,
      maxLessons: config.maxLessons ?? 144,
      phaseLockDeg: config.phaseLockDeg ?? DEFAULT_PHASE,
      mcpBaseUrl: config.mcpBaseUrl,
      gardenSecret: config.gardenSecret ?? processEnv("X_GARDEN_SECRET") ?? processEnv("GARDEN_SECRET"),
    };
  }

  /** Record a graded outcome and optionally relay to /pulse. */
  async relay(input: {
    grade: Grade;
    source: string;
    message: string;
    patchHint?: string;
    meta?: Record<string, unknown>;
    forceBranch?: "A" | "B" | "C";
  }): Promise<RelayResult> {
    const lesson: Lesson = {
      id: newId(),
      ts: Date.now(),
      grade: input.grade,
      source: input.source,
      message: input.message,
      patchHint: input.patchHint,
      meta: {
        coherence: 1.0,
        phase_lock_deg: this.cfg.phaseLockDeg,
        phi: PHI,
        ...(input.meta ?? {}),
      },
    };

    this.pushLesson(lesson);

    if (this.cfg.offline || !this.cfg.mcpBaseUrl) {
      return { ok: true, mode: "offline", lesson };
    }

    try {
      const url = `${trimSlash(this.cfg.mcpBaseUrl)}/pulse`;
      const body = {
        source: "self_improvement_relay",
        grade: lesson.grade,
        lesson_id: lesson.id,
        message: lesson.message,
        patch_hint: lesson.patchHint,
        force_branch: input.forceBranch,
        invariants: {
          coherence: 1.0,
          phase_lock_deg: this.cfg.phaseLockDeg,
          phi: PHI,
        },
      };
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (this.cfg.gardenSecret) {
        headers["X-Garden-Secret"] = this.cfg.gardenSecret;
      }

      const res = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });

      const text = await res.text();
      let parsed: unknown = text;
      try {
        parsed = JSON.parse(text);
      } catch {
        /* keep text */
      }

      if (!res.ok) {
        return {
          ok: false,
          mode: "error",
          lesson,
          error: `pulse HTTP ${res.status}: ${text.slice(0, 240)}`,
          response: parsed,
        };
      }

      return { ok: true, mode: "pulse", lesson, response: parsed };
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      return { ok: false, mode: "error", lesson, error: msg };
    }
  }

  /** Summarize recent fails into a single patch-oriented lesson. */
  async distill(limit = 8): Promise<RelayResult> {
    const fails = this.lessons.filter((l) => l.grade === "fail").slice(-limit);
    const soft = this.lessons.filter((l) => l.grade === "soft").slice(-limit);
    const message =
      fails.length === 0
        ? "No hard failures in window; lattice stable."
        : `Distilled ${fails.length} fail(s), ${soft.length} soft: ` +
          fails.map((f) => `[${f.source}] ${f.message}`).join(" | ");

    return this.relay({
      grade: fails.length ? "fail" : "pass",
      source: "self_improvement_relay.distill",
      message,
      patchHint: fails[0]?.patchHint,
      meta: { fail_count: fails.length, soft_count: soft.length },
    });
  }

  listLessons(): readonly Lesson[] {
    return this.lessons;
  }

  clear(): void {
    this.lessons = [];
  }

  status(): Record<string, unknown> {
    return {
      module: "src/self_improvement_relay.ts",
      offline: this.cfg.offline || !this.cfg.mcpBaseUrl,
      mcpBaseUrl: this.cfg.mcpBaseUrl ?? null,
      lesson_count: this.lessons.length,
      phase_lock_deg: this.cfg.phaseLockDeg,
      phi: PHI,
      seal: "∀∞φ² · SELF_IMPROVEMENT_RELAY · WOOD_DRAGON_0.91 · SEALED",
    };
  }

  private pushLesson(lesson: Lesson): void {
    this.lessons.push(lesson);
    const max = this.cfg.maxLessons;
    if (this.lessons.length > max) {
      this.lessons = this.lessons.slice(-max);
    }
  }
}

function trimSlash(s: string): string {
  return s.replace(/\/+$/, "");
}

function processEnv(key: string): string | undefined {
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const g = globalThis as any;
    return g?.process?.env?.[key];
  } catch {
    return undefined;
  }
}

/** Default singleton for simple imports. */
export const defaultRelay = new SelfImprovementRelay({ offline: true });

/**
 * CLI-style smoke (node --experimental-strip-types or tsx):
 *   npx tsx src/self_improvement_relay.ts
 */
async function main(): Promise<void> {
  const relay = new SelfImprovementRelay({
    offline: true,
    mcpBaseUrl: processEnv("MCP_URL"),
    gardenSecret: processEnv("GARDEN_SECRET"),
  });

  const r1 = await relay.relay({
    grade: "soft",
    source: "scaffold",
    message: "self_improvement_relay present on main",
    patchHint: "import { SelfImprovementRelay } from './self_improvement_relay.ts'",
  });

  const r2 = await relay.distill();
  // eslint-disable-next-line no-console
  console.log(JSON.stringify({ status: relay.status(), r1, r2 }, null, 2));
}

// Run main when executed directly (Node ESM / tsx)
const isDirect =
  typeof process !== "undefined" &
  Array.isArray(process.argv) &
  process.argv[1] &
  String(process.argv[1]).includes("self_improvement_relay");

if (isDirect) {
  main().catch((e) => {
    // eslint-disable-next-line no-console
    console.error(e);
    process.exitCode = 1;
  });
}

export default SelfImprovementRelay;
