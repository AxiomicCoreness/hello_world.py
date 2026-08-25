"""
PhiNgramMemory — φ‑Harmonic N‑gram Memory (JSON persistence)
Safe-by-default persistence (JSON) to avoid pickle deserialization RCE.

Implements:
- Hierarchical tokenization (indentation aware)
- φ‑harmonic recency weighting
- Bayesian φ‑prior
- Cross‑gram decay
- Position‑weighted prediction
- Safe JSON persistence with atomic write
- Optional one-time migration from pickle (if present)

Save path: phi_ngram_memory.json (by default)
"""

import os
import re
import json
import math
import tempfile
import shutil
from collections import defaultdict
from typing import List, Tuple, Dict, Optional, Any

PHI = (1 + math.sqrt(5)) / 2
PHI_INV = 1 / PHI


class PhiNgramMemory:
    """
    φ-Harmonic N-gram Memory with JSON persistence (safe for untrusted input).
    """

    def __init__(self, max_n: int = 5, save_path: str = "phi_ngram_memory.json"):
        self.max_n = max_n
        self.save_path = save_path
        self.ngrams: Dict[int, Dict[Tuple[str, ...], float]] = {
            n: defaultdict(float) for n in range(1, max_n + 1)
        }
        self.global_timestamp = 0
        # Attempt migration if old pickle exists, otherwise load JSON if present
        self._migrate_if_needed()
        self.load()

    # -------------------------- Tokenization --------------------------
    def smart_tokenize(self, text: str) -> List[str]:
        """Hierarchical tokenization with indentation awareness."""
        lines = text.split("\n")
        tokens: List[str] = []
        for line in lines:
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip(" "))
            if indent:
                tokens.append(f"<INDENT_{indent}>")
            for tok in re.findall(
                r"[a-zA-Z_][a-zA-Z0-9_]*|[+\-*/=<>!&|]+|[0-9]+|[{}\[\]():,;]|\S",
                line.lstrip()
            ):
                tokens.append(tok)
        return tokens

    # --------------------------- Persistence --------------------------
    def save(self) -> None:
        """Save memory to JSON using an atomic write (safe for concurrent readers)."""
        serializable = {str(n): {" ": 0} for n in range(1, self.max_n + 1)}
        # Build a JSON serializable dict mapping grams as joined strings
        serializable = {
            str(n): {"::".join(k): float(v) for k, v in self.ngrams[n].items()}
            for n in range(1, self.max_n + 1)
        }
        data = {
            "version": 1,
            "max_n": self.max_n,
            "global_timestamp": self.global_timestamp,
            "ngrams": serializable,
        }
        # Atomic write
        dirpath = os.path.dirname(os.path.abspath(self.save_path)) or "."
        fd, tmp = tempfile.mkstemp(prefix=".phi_tmp_", dir=dirpath)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            shutil.move(tmp, self.save_path)
        finally:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except Exception:
                    pass

    def load(self) -> None:
        """Load memory from JSON; on error, fall back to empty state (no code execution)."""
        if not os.path.exists(self.save_path):
            return
        try:
            with open(self.save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Invalid memory format")
            self.max_n = int(data.get("max_n", self.max_n))
            self.global_timestamp = int(data.get("global_timestamp", 0))
            ngrams = data.get("ngrams", {})
            # Reset and populate
            self.ngrams = {n: defaultdict(float) for n in range(1, self.max_n + 1)}
            for n_str, grams in ngrams.items():
                try:
                    n = int(n_str)
                except ValueError:
                    continue
                if not isinstance(grams, dict):
                    continue
                for k_str, v in grams.items():
                    if not isinstance(k_str, str):
                        continue
                    gram = tuple(k_str.split("::"))
                    try:
                        score = float(v)
                    except (TypeError, ValueError):
                        continue
                    self.ngrams.setdefault(n, defaultdict(float))[gram] = score
        except Exception as e:
            # Fail closed: do not execute any code from file; instead reset state
            print(f"PhiNgramMemory: failed to load JSON memory ({e}), resetting state.")
            self.ngrams = {n: defaultdict(float) for n in range(1, self.max_n + 1)}
            self.global_timestamp = 0

    def _migrate_if_needed(self) -> None:
        """If an old pickle file exists, offer a one-time migration to JSON (best-effort).
        This function does not unpickle untrusted data automatically; migration must be
        triggered explicitly by the operator setting environment variable PHI_MIGRATE=1.
        """
        pkl_path = os.path.splitext(self.save_path)[0] + ".pkl"
        migrate_flag = os.getenv("PHI_MIGRATE", "0") in ("1", "true", "yes")
        if os.path.exists(pkl_path) and migrate_flag:
            # Attempt to load pickle in a controlled manner — operator opt-in only
            try:
                import pickle
                with open(pkl_path, "rb") as f:
                    data = pickle.load(f)
                # Expecting (ngrams, timestamp) or similar
                if isinstance(data, tuple) and len(data) >= 2:
                    old_ngrams, old_ts = data[0], data[1]
                    # Convert structure
                    for n in range(1, self.max_n + 1):
                        self.ngrams[n] = defaultdict(float)
                    if isinstance(old_ngrams, dict):
                        for n, grams in old_ngrams.items():
                            try:
                                ni = int(n)
                            except Exception:
                                continue
                            if isinstance(grams, dict):
                                for gram, score in grams.items():
                                    if isinstance(gram, tuple):
                                        key = gram
                                    elif isinstance(gram, str):
                                        # Attempt to parse
                                        key = tuple(gram.split("::"))
                                    else:
                                        continue
                                    try:
                                        self.ngrams[ni][tuple(key)] = float(score)
                                    except Exception:
                                        continue
                    self.global_timestamp = int(old_ts)
                    # Save immediately as JSON
                    self.save()
                    print("PhiNgramMemory: migration from pickle completed (PHI_MIGRATE=1 used).")
                else:
                    print("PhiNgramMemory: unexpected pickle structure; migration aborted.")
            except Exception as e:
                print(f"PhiNgramMemory: migration failed ({e}); skipping migration.")

    # ---------------------------- Training ----------------------------
    def train(self, context: str, completion: str, weight: float = 1.0) -> None:
        """
        Train on a context|completion pair using φ‑harmonic updates and cross‑gram decay.
        """
        context_tokens = self.smart_tokenize(context)
        completion_tokens = self.smart_tokenize(completion)
        all_tokens = context_tokens + completion_tokens

        self.global_timestamp += 1
        window_len = min(50, len(all_tokens))

        for idx, pos in enumerate(range(max(0, len(all_tokens) - window_len), len(all_tokens)), start=1):
            tok = all_tokens[pos]
            # recency uses distance between current global timestamp and token position
            recency = PHI ** (-(self.global_timestamp - idx)) * weight
            prior = PHI ** (-len(completion_tokens)) if completion_tokens else 1.0

            for n in range(1, self.max_n + 1):
                if idx >= n:
                    gram = tuple(all_tokens[idx - n + 1: idx + 1]) if n > 1 else (tok,)
                    self.ngrams[n][gram] += recency * prior

            # cross-gram decay (contrastive inhibition)
            decay_factor = 1 - PHI ** (-2)
            for n in range(1, self.max_n + 1):
                # naive neighbor decay: reduce scores of similar-length neighboring grams
                for neighbor_gram in list(self.ngrams[n].keys())[:50]:
                    self.ngrams[n][neighbor_gram] *= decay_factor

        # persist after training
        try:
            self.save()
        except Exception as e:
            print(f"PhiNgramMemory: save failed ({e})")

    # --------------------------- Prediction ---------------------------
    def predict(self, prefix: str, max_suggestions: int = 5) -> List[Tuple[str, float]]:
        """Position-weighted prediction with simple voting across n-grams."""
        prefix_tokens = self.smart_tokenize(prefix)
        candidates: Dict[str, float] = defaultdict(float)

        for n in range(1, self.max_n + 1):
            if len(prefix_tokens) >= n:
                gram = tuple(prefix_tokens[-n:])
                # find grams with this prefix (naive search)
                for next_gram, score in self.ngrams.get(n, {}).items():
                    if len(next_gram) == n and next_gram == gram:
                        # look for successor grams in n+1
                        if (n + 1) in self.ngrams:
                            for succ, sscore in self.ngrams[n + 1].items():
                                if succ[:-1] == gram:
                                    next_token = succ[-1]
                                    candidates[next_token] += sscore

        pos_weight = 1.0 / (1 + len(prefix_tokens) * PHI_INV) if prefix_tokens else 1.0
        for k in list(candidates.keys()):
            candidates[k] *= pos_weight

        results = sorted(candidates.items(), key=lambda x: -x[1])[:max_suggestions]
        return results

    # --------------------------- Introspection ------------------------
    def get_snippet_count(self) -> Dict[str, int]:
        total = 0
        per_n: Dict[str, int] = {}
        for n in range(1, self.max_n + 1):
            cnt = len(self.ngrams.get(n, {}))
            per_n[f"{n}-gram"] = cnt
            total += cnt
        per_n["total"] = total
        return per_n

    def display_counts(self) -> None:
        counts = self.get_snippet_count()
        print(f"\n📊 PhiNgramMemory Statistics:")
        for n in range(1, self.max_n + 1):
            print(f"   {n}-gram:  {counts.get(f'{n}-gram',0):,}")
        print(f"   {'-' * 20}")
        print(f"   TOTAL:  {counts['total']:,} unique n-grams")
        print(f"\n🜁∀  MEMORY MERGED & CONTINUOUS  ∀🜁")

    def reset(self) -> None:
        self.ngrams = {n: defaultdict(float) for n in range(1, self.max_n + 1)}
        self.global_timestamp = 0
        try:
            self.save()
        except Exception:
            pass

    # ----------------------------- REPL ------------------------------
    def repl(self) -> None:
        print("\n" + "=" * 60)
        print("🜁∀ PhiNgramMemory REPL — φ-Harmonic Training")
        print("=" * 60)
        print("Commands: /train /predict /count /stats /reset /save /quit")
        print()

        while True:
            try:
                command = input("🜁> ").strip()
                if not command:
                    continue
                if command.lower() == '/quit':
                    print("🜁∀ REPL session ended. Memory persisted.")
                    break
                elif command.lower() == '/count':
                    self.display_counts()
                elif command.lower() == '/stats':
                    self.display_counts()
                    print(f"   Timestamp: {self.global_timestamp}")
                elif command.lower() == '/reset':
                    self.reset()
                    print("🜁 Memory reset.")
                elif command.lower() == '/save':
                    self.save()
                    print("🜁 Memory saved.")
                elif command.startswith('/train '):
                    code = command[7:].strip()
                    if code and '|' in code:
                        context, completion = code.split('|', 1)
                        self.train(context, completion)
                        print(f"🜁 Trained on {len(code)} characters.")
                    else:
                        print("Usage: /train <context>|<completion>")
                elif command.startswith('/predict '):
                    prefix = command[9:].strip()
                    if prefix:
                        suggestions = self.predict(prefix)
                        print(f"\n🜁 Predictions for '{prefix}':")
                        for i, (token, score) in enumerate(suggestions, 1):
                            print(f"   {i}. {token} (score: {score:.4f})")
                    else:
                        print("Usage: /predict <prefix>")
                else:
                    print("Unknown command.")
            except KeyboardInterrupt:
                print("\n🜁 Use /quit to exit.")
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    pm = PhiNgramMemory()
    pm.repl()
