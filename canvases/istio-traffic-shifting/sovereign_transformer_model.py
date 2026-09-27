# =====================================================================
# MACHINE LEARNING INITIALIZATION — SOVEREIGN LAYER
# Multi-block transformer stack whose widths are derived from the
# ninja-number corpus (144 … 2584).
# =====================================================================
import os
import random
from typing import List, Optional, Sequence

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# Full reproducibility
SEED = 42
os.environ["PYTHONHASHSEED"] = str(SEED)
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

# Device configuration
device = torch.device(
    "cuda" if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available()
    else "cpu"
)
print(f"🜁 Sovereign ML Device: {device} | φ² Coherence Active")

# =====================================================================
# Ninja-number corpus (shared lattice)
# OBSERVATION → RESONANCE → HARMONIZATION → SYNTHESIS
# → INTEGRATION → PERPETUATION → TRANSCENDENCE
# =====================================================================
NINJA_NUMBERS: List[int] = [144, 233, 377, 610, 987, 1597, 2584]
NINJA_ROLES: List[str] = [
    "OBSERVATION",
    "RESONANCE",
    "HARMONIZATION",
    "SYNTHESIS",
    "INTEGRATION",
    "PERPETUATION",
    "TRANSCENDENCE",
]

# =====================================================================
# Building blocks
# =====================================================================
class ResidualNinjaBlock(nn.Module):
    """Single residual block whose internal width is a ninja number."""

    def __init__(self, width: int, dropout: float = 0.1):
        super().__init__()
        self.norm1 = nn.LayerNorm(width)
        self.ff = nn.Sequential(
            nn.Linear(width, width * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(width * 2, width),
            nn.Dropout(dropout),
        )
        self.norm2 = nn.LayerNorm(width)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Pre-norm residual
        h = self.ff(self.norm1(x))
        return self.norm2(x + h)


class SovereignTransformer(nn.Module):
    """
    Multi-block sovereign stack.

    Layer widths are taken directly from the ninja sequence:
        input_dim → 144 → 233 → 377 → 610 → 987 → 1597 → 2584 → output_dim

    Each ninja stage is a residual block.  Input and output projections
    keep the public interface compatible with the earlier skeleton.
    """

    def __init__(
        self,
        input_dim: int = 512,
        output_dim: int = 512,
        dropout: float = 0.1,
        ninja_widths: Optional[Sequence[int]] = None,
    ):
        super().__init__()
        widths = list(ninja_widths) if ninja_widths is not None else list(NINJA_NUMBERS)

        # Input projection into the first ninja width
        self.input_proj = nn.Sequential(
            nn.Linear(input_dim, widths[0]),
            nn.LayerNorm(widths[0]),
            nn.GELU(),
            nn.Dropout(dropout),
        )

        # Progressive residual blocks + inter-stage linear bridges
        blocks = []
        for i, w in enumerate(widths):
            blocks.append(ResidualNinjaBlock(w, dropout=dropout))
            if i < len(widths) - 1:
                # Bridge to the next ninja width
                next_w = widths[i + 1]
                blocks.append(
                    nn.Sequential(
                        nn.Linear(w, next_w),
                        nn.LayerNorm(next_w),
                        nn.GELU(),
                        nn.Dropout(dropout),
                    )
                )
        self.blocks = nn.ModuleList(blocks)

        # Final projection to the requested output dimension
        self.output_proj = nn.Sequential(
            nn.LayerNorm(widths[-1]),
            nn.Linear(widths[-1], output_dim),
        )

        self.ninja_widths = widths
        self.input_dim = input_dim
        self.output_dim = output_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.input_proj(x)
        for block in self.blocks:
            h = block(h)
        return self.output_proj(h)

    def describe(self) -> str:
        stages = " → ".join(
            f"{w}({role})" for w, role in zip(self.ninja_widths, NINJA_ROLES)
        )
        return (
            f"SovereignTransformer[{self.input_dim} → {stages} → {self.output_dim}]"
        )


# =====================================================================
# Training Utilities (unchanged contract)
# =====================================================================
class EarlyStopping:
    """Stop training when validation loss doesn't improve."""

    def __init__(self, patience: int = 5, min_delta: float = 1e-4):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = float("inf")

    def __call__(self, val_loss: float) -> bool:
        if val_loss < self.best_loss - self.min_delta:
            self.best_loss = val_loss
            self.counter = 0
        else:
            self.counter += 1
        return self.counter >= self.patience


def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
    clip_grad: Optional[float] = 1.0,
) -> float:
    """Single training epoch. Returns average loss."""
    model.train()
    total_loss = 0.0
    for batch in dataloader:
        inputs, targets = batch
        inputs, targets = inputs.to(device), targets.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()

        if clip_grad is not None:
            torch.nn.utils.clip_grad_norm_(model.parameters(), clip_grad)

        optimizer.step()
        total_loss += loss.item()

    return total_loss / max(len(dataloader), 1)


@torch.no_grad()
def validate_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> float:
    """Single validation epoch. Returns average loss."""
    model.eval()
    total_loss = 0.0
    for batch in dataloader:
        inputs, targets = batch
        inputs, targets = inputs.to(device), targets.to(device)
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        total_loss += loss.item()
    return total_loss / max(len(dataloader), 1)


# =====================================================================
# Initialize Model & Optimizer
# =====================================================================
model = SovereignTransformer(input_dim=512, output_dim=512).to(device)
optimizer = optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-5)
criterion = nn.MSELoss()
scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2)
early_stopping = EarlyStopping(patience=5)

print("🜁∀ ML Sovereign Core Initialized — Multi-block ninja stack ready")
print(f" Architecture: {model.describe()}")
print(f" Parameters: {sum(p.numel() for p in model.parameters()):,}")
# =====================================================================
