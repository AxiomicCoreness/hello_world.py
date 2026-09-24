# =====================================================================
# MACHINE LEARNING INITIALIZATION — SOVEREIGN LAYER (CORRECTED)
# =====================================================================
import os
import random
from typing import Optional

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
# Sovereign Transformer Model
# =====================================================================
class SovereignTransformer(nn.Module):
    """Minimal sovereign φ‑harmonic model skeleton"""
    def __init__(self, input_dim=512, hidden_dim=1024, output_dim=512, dropout=0.1):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, output_dim),
        )

    def forward(self, x):
        return self.layers(x)

# =====================================================================
# Training Utilities
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
model = SovereignTransformer(input_dim=512, hidden_dim=1024, output_dim=512).to(device)
optimizer = optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-5)
criterion = nn.MSELoss()
scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2)
early_stopping = EarlyStopping(patience=5)

print("🜁∀ ML Sovereign Core Initialized — Model ready on device")
print(f" Parameters: {sum(p.numel() for p in model.parameters()):,}")
# =====================================================================
```

**Changes made**
- Fixed all indentation (CUDA seed block, device construction, method bodies).
- Removed the stray non-code text that was injected inside `train_epoch`.
- Added `max(..., 1)` guards to avoid division-by-zero on empty loaders.
- Made `clip_grad` check explicit (`is not None`).
- Code is now syntactically valid (AST-clean).
