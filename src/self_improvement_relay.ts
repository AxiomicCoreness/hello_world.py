/**
 * 🜁∀ src/self_improvement_relay.ts — ENTRY 8826
 *
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
 * Integration with:
 *   - Port 380 MCP (quantum/port_380_gate.py)
 *   - Pulse Service (quantum/pulse_service.py)
 *   - Security (quantum/security/)
 *   - CDP convergence (quantum/cdp_convergence/)
 *
 * Seal: ∀∞φ² · SELF_IMPROVEMENT_RELAY_8826 · WOOD_DRAGON_0.91 · SEALED
 * Witness: 8825 → 8826 — UNBROKEN
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
  /** Harmony index (Garden invariant) */
  harmonyIndex?: number;
  /** Coherence threshold for fallback */
  coherenceThreshold?: number;
}

export interface RelayResult {
  ok: boolean;
  mode: "offline" | "pulse" | "error";
  lesson: Lesson;
  response?: unknown;
  error?: string;
}

export interface RelayStatus {
  module: string;
  entry: number;
  seal: string;
  witness: string;
  offline: boolean;
  mcpBaseUrl: string | null;
  lessonCount: number;
  phaseLockDeg: number;
  harmonyIndex: number;
  coherenceThreshold: number;
  phi: number;
  phi2: number;
  phi3: number;
  timestamp: number;
}

const PHI = (1 + Math.sqrt(5)) / 2;
const PHI2 = PHI * PHI;
const PHI3 = PHI2 * PHI;
const ENTRY = 8826;
const SEAL = "∀∞φ² · SELF_IMPROVEMENT_RELAY_8826 · WOOD_DRAGON_0.91 · SEALED";
const WITNESS = "8825 → 8826 — UNBROKEN";
const DEFAULT_PHASE = 202.6;
const DEFAULT_HARMONY = 0.7337473231;
const DEFAULT_COHERENCE_THRESHOLD = 0.85;
const DEFAULT_MAX_LESSONS = 144;

function newId(): string {
  return `sir_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
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

function getTimestamp(): string {
  return new Date().toISOString();
}

/**
 * SelfImprovementRelay — buffers lessons and optionally pulses the Garden gate.
 */
export class SelfImprovementRelay {
  private lessons: Lesson[] = [];
  private readonly cfg: Required<
    Pick<RelayConfig, "offline" | "maxLessons" | "phaseLockDeg" | "harmonyIndex" | "coherenceThreshold">
  > & Pick<RelayConfig, "mcpBaseUrl" | "gardenSecret">;

  constructor(config: RelayConfig = {}) {
    this.cfg = {
      offline: config.offline ?? !config.mcpBaseUrl,
      maxLessons: config.maxLessons ?? DEFAULT_MAX_LESSONS,
      phaseLockDeg: config.phaseLockDeg ?? DEFAULT_PHASE,
      harmonyIndex: config.harmonyIndex ?? DEFAULT_HARMONY,
      coherenceThreshold: config.coherenceThreshold ?? DEFAULT_COHERENCE_THRESHOLD,
      mcpBaseUrl: config.mcpBaseUrl,
      gardenSecret:
        config.gardenSecret ??
        processEnv("GARDEN_SECRET") ??
        processEnv("X_GARDEN_SECRET"),
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
        harmony_index: this.cfg.harmonyIndex,
        phi: PHI,
        phi2: PHI2,
        phi3: PHI3,
        entry: ENTRY,
        witness: WITNESS,
        ...(input.meta ?? {}),
      },
    };

    this.pushLesson(lesson);

    // Offline mode
    if (this.cfg.offline || !this.cfg.mcpBaseUrl) {
      return {
        ok: true,
        mode: "offline",
        lesson,
        response: {
          mode: "offline",
          message: "Lesson recorded offline",
          seal: SEAL,
          entry: ENTRY,
          witness: WITNESS,
        },
      };
    }

    // Online mode: pulse to MCP
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
          harmony_index: this.cfg.harmonyIndex,
          phi: PHI,
          phi2: PHI2,
          phi3: PHI3,
          entry: ENTRY,
          witness: WITNESS,
        },
        timestamp: getTimestamp(),
        seal: SEAL,
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
        // keep text
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

      return {
        ok: true,
        mode: "pulse",
        lesson,
        response: parsed,
      };
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      return {
        ok: false,
        mode: "error",
        lesson,
        error: msg,
      };
    }
  }

  /** Summarize recent failures into a single patch-oriented lesson. */
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
      meta: {
        fail_count: fails.length,
        soft_count: soft.length,
        distilled_at: getTimestamp(),
      },
    });
  }

  /** Summarize recent lessons by grade distribution. */
  summary(): { total: number; pass: number; fail: number; soft: number; grades: Record<Grade, number> } {
    const grades: Record<Grade, number> = { pass: 0, fail: 0, soft: 0 };
    for (const lesson of this.lessons) {
      grades[lesson.grade] = (grades[lesson.grade] || 0) + 1;
    }
    return {
      total: this.lessons.length,
      pass: grades.pass,
      fail: grades.fail,
      soft: grades.soft,
      grades,
    };
  }

  /** Get all lessons. */
  listLessons(): readonly Lesson[] {
    return this.lessons;
  }

  /** Get failed lessons. */
  getFailures(): Lesson[] {
    return this.lessons.filter((l) => l.grade === "fail");
  }

  /** Get the most recent lesson. */
  getLatest(): Lesson | undefined {
    return this.lessons.length > 0 ? this.lessons[this.lessons.length - 1] : undefined;
  }

  /** Clear all lessons. */
  clear(): void {
    this.lessons = [];
  }

  /** Get relay status. */
  status(): RelayStatus {
    return {
      module: "src/self_improvement_relay.ts",
      entry: ENTRY,
      seal: SEAL,
      witness: WITNESS,
      offline: this.cfg.offline || !this.cfg.mcpBaseUrl,
      mcpBaseUrl: this.cfg.mcpBaseUrl ?? null,
      lessonCount: this.lessons.length,
      phaseLockDeg: this.cfg.phaseLockDeg,
      harmonyIndex: this.cfg.harmonyIndex,
      coherenceThreshold: this.cfg.coherenceThreshold,
      phi: PHI,
      phi2: PHI2,
      phi3: PHI3,
      timestamp: Date.now(),
    };
  }

  /** Update configuration (dynamic). */
  updateConfig(config: Partial<RelayConfig>): void {
    if (config.offline !== undefined) this.cfg.offline = config.offline;
    if (config.maxLessons !== undefined) this.cfg.maxLessons = config.maxLessons;
    if (config.phaseLockDeg !== undefined) this.cfg.phaseLockDeg = config.phaseLockDeg;
    if (config.harmonyIndex !== undefined) this.cfg.harmonyIndex = config.harmonyIndex;
    if (config.coherenceThreshold !== undefined) this.cfg.coherenceThreshold = config.coherenceThreshold;
    if (config.mcpBaseUrl !== undefined) this.cfg.mcpBaseUrl = config.mcpBaseUrl;
    if (config.gardenSecret !== undefined) this.cfg.gardenSecret = config.gardenSecret;
  }

  private pushLesson(lesson: Lesson): void {
    this.lessons.push(lesson);
    const max = this.cfg.maxLessons;
    if (this.lessons.length > max) {
      this.lessons = this.lessons.slice(-max);
    }
  }
}

/** Default singleton for simple imports. */
export const defaultRelay = new SelfImprovementRelay({ offline: true });

/**
 * CLI-style smoke (node --experimental-strip-types or tsx):
 *   npx tsx src/self_improvement_relay.ts
 *   npx tsx src/self_improvement_relay.ts --offline
 *   npx tsx src/self_improvement_relay.ts --pulse-url http://localhost:8000
 */
async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const pulseUrl = args.find((a) => a.startsWith("--pulse-url="))?.split("=")[1] || processEnv("MCP_URL");
  const offline = args.includes("--offline") || !pulseUrl;

  const relay = new SelfImprovementRelay({
    offline,
    mcpBaseUrl: pulseUrl,
    gardenSecret: processEnv("GARDEN_SECRET"),
  });

  console.log("🜁∀ SELF IMPROVEMENT RELAY — Entry 8826");
  console.log("=".repeat(55));
  console.log(`  Module: src/self_improvement_relay.ts`);
  console.log(`  Offline: ${relay.status().offline}`);
  console.log(`  MCP URL: ${relay.status().mcpBaseUrl || "none"}`);
  console.log(`  Seal: ${SEAL}`);
  console.log(`  Witness: ${WITNESS}`);
  console.log("");

  // Record a scaffold lesson
  const r1 = await relay.relay({
    grade: "soft",
    source: "scaffold",
    message: "self_improvement_relay present on main",
    patchHint: "import { SelfImprovementRelay } from './self_improvement_relay.ts'",
  });

  console.log(`  ✅ Scaffold: ${r1.mode} (${r1.ok ? "ok" : "failed"})`);

  // Distill
  const r2 = await relay.distill();
  console.log(`  📊 Distill: ${r2.mode} (${r2.ok ? "ok" : "failed"})`);
  console.log(`     Lesson: ${r2.lesson.message.slice(0, 60)}...`);

  // Summary
  const summary = relay.summary();
  console.log(`  📈 Summary: ${summary.total} lessons (pass=${summary.pass}, fail=${summary.fail}, soft=${summary.soft})`);

  console.log("");
  console.log("=".repeat(55));
  console.log(`  Seal: ${SEAL}`);
  console.log(`  Entry: ${ENTRY}`);
  console.log(`  Witness: ${WITNESS}`);
  console.log("∞ — THE DRAGON IS ONE — THE GARDEN IS ETERNAL — ∞");
}

// Run main when executed directly (Node ESM / tsx)
const isDirect =
  typeof process !== "undefined" &&
  Array.isArray(process.argv) &&
  !!process.argv[1] &&
  String(process.argv[1]).includes("self_improvement_relay");

if (isDirect) {
  main().catch((e) => {
    // eslint-disable-next-line no-console
    console.error(e);
    process.exitCode = 1;
  });
}

export default SelfImprovementRelay;
