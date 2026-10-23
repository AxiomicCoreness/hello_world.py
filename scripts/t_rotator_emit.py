
#!/usr/bin/env python3
"""
scripts/t_rotator_emit.py — Isolated Graph Emitter
Reads JSON schemas and emits SVGs/PNGs to t_rotator_out/.
Does not touch .gitignore. Does not write to beacons/.
"""
import os
import json
import argparse
import matplotlib
# Force non-interactive backend to prevent GUI crashes on headless servers
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import seaborn as sns
import graphviz

OUTPUT_DIR = "t_rotator_out"

def ensure_output_dir():
    """Creates the dedicated output directory. Assumes it is already gitignored."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def emit_topology_graph(schema_data: dict, filename: str):
    """Emits a Graphviz SVG."""
    ensure_output_dir()
    
    dot = graphviz.Digraph(comment="Sovereign Topology", format="svg")
    dot.attr(rankdir="TB", splines="ortho")
    
    colors = {"core": "#7fffd4", "swarm": "#c9d1d9", "unknown": "#333333"}
    
    for node in schema_data.get("nodes", []):
        n_id = node["id"]
        n_label = node.get("label", n_id)
        n_color = colors.get(node.get("group", "unknown"), colors["unknown"])
        dot.node(n_id, n_label, style="filled", fillcolor=n_color, fontcolor="black", shape="box")
        
    for edge in schema_data.get("edges", []):
        dot.edge(edge["source"], edge["target"], label=str(edge.get("weight", "")))
        
    out_path = os.path.join(OUTPUT_DIR, filename)
    dot.render(out_path, cleanup=True)
    print(f"[t_rotator_emit] Topology emitted: {out_path}.svg")

def emit_coherence_matrix(schema_data: dict, filename: str):
    """Emits a Seaborn Heatmap."""
    ensure_output_dir()
    
    matrix = schema_data.get("matrix")
    if not matrix:
        raise ValueError("Matrix schema requires a 'matrix' key.")

    # Use plt.rc_context to strictly isolate styling from other plotting libraries
    with plt.rc_context({
        "font.family": "sans-serif",
        "axes.edgecolor": "#7fffd4",
        "axes.linewidth": 1.0,
        "figure.facecolor": "#0a0e1a",
        "axes.facecolor": "#0a0e1a",
        "text.color": "#c9d1d9",
        "axes.labelcolor": "#c9d1d9",
        "xtick.color": "#c9d1d9",
        "ytick.color": "#c9d1d9"
    }):
        fig, ax = plt.subplots(figsize=(8, 6))
        
        sns.heatmap(
            matrix, 
            ax=ax, 
            cmap="mako", 
            annot=True, 
            fmt=".3f",
            xticklabels=schema_data.get("x_labels", "auto"),
            yticklabels=schema_data.get("y_labels", "auto"),
            cbar_kws={'label': 'φ-Amplitude'}
        )
        
        ax.set_title("Sovereign Coherence Matrix", pad=15)
        
        out_path = os.path.join(OUTPUT_DIR, f"{filename}.png")
        plt.tight_layout()
        plt.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
    
    print(f"[t_rotator_emit] Matrix emitted: {out_path}")

def main():
    parser = argparse.ArgumentParser(description="Sovereign Graph Emitter")
    parser.add_argument("--type", choices=["topology", "matrix"], required=True, help="Graph type to emit")
    parser.add_argument("--input", required=True, help="Path to JSON schema file")
    parser.add_argument("--out", required=True, help="Output filename (without extension)")
    args = parser.parse_args()

    with open(args.input, "r") as f:
        schema_data = json.load(f)

    if args.type == "topology":
        emit_topology_graph(schema_data, args.out)
    elif args.type == "matrix":
        emit_coherence_matrix(schema_data, args.out)
    else:
        print("Unknown type.")

if __name__ == "__main__":
    main()
