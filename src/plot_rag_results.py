#!/usr/bin/env python3
"""Generate publication-quality figures from RAG AB test reports."""

import json
import sys
from pathlib import Path
from typing import Dict, Any

# Try matplotlib with non-interactive backend
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def load_report(path: Path) -> Dict[str, Any]:
    """Load JSON report."""
    return json.loads(path.read_text(encoding="utf-8"))


def plot_recall_comparison(report_path: Path, output_path: Path) -> None:
    """
    Plot Recall@1, @3, @5 comparison for vector-only vs hybrid.
    
    This creates a grouped bar chart suitable for thesis figures.
    """
    report = load_report(report_path)
    arms = report.get("arms", {})
    a_data = arms.get("A_vector_only", {})
    b_data = arms.get("B_hybrid_rerank", {})
    
    source_recall_a = a_data.get("source_recall_at", {})
    source_recall_b = b_data.get("source_recall_at", {})
    
    # Extract recall values for k=1,3,5
    k_values = ["1", "3", "5"]
    a_values = [source_recall_a.get(k, 0) for k in k_values]
    b_values = [source_recall_b.get(k, 0) for k in k_values]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    
    x = np.arange(len(k_values))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, a_values, width, label='A: Vector-Only', color='#1f77b4', alpha=0.8)
    bars2 = ax.bar(x + width/2, b_values, width, label='B: Hybrid+Rerank', color='#ff7f0e', alpha=0.8)
    
    # Formatting
    ax.set_xlabel('Recall@K', fontsize=12, fontweight='bold')
    ax.set_ylabel('Recall Score', fontsize=12, fontweight='bold')
    ax.set_title('RAG Retrieval Performance Comparison\n(Natural Language Dataset, 80 queries)', 
                 fontsize=13, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels([f'@{k}' for k in k_values])
    ax.set_ylim(0.7, 1.02)
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved figure: {output_path}")
    plt.close()


def plot_metric_comparison(report_path: Path, output_path: Path) -> None:
    """
    Plot all key metrics in one comprehensive comparison.
    """
    report = load_report(report_path)
    arms = report.get("arms", {})
    a_data = arms.get("A_vector_only", {})
    b_data = arms.get("B_hybrid_rerank", {})
    
    metrics = {
        'Source\nHitRate': (a_data.get("source_hitrate", 0), b_data.get("source_hitrate", 0)),
        'Keyword\nHitRate': (a_data.get("keyword_hitrate", 0), b_data.get("keyword_hitrate", 0)),
        'MRR': (a_data.get("mrr", 0), b_data.get("mrr", 0)),
        'nDCG': (a_data.get("ndcg", 0), b_data.get("ndcg", 0)),
        'Recall@1': (a_data.get("source_recall_at", {}).get("1", 0), 
                     b_data.get("source_recall_at", {}).get("1", 0)),
        'Recall@3': (a_data.get("source_recall_at", {}).get("3", 0), 
                     b_data.get("source_recall_at", {}).get("3", 0)),
        'Recall@5': (a_data.get("source_recall_at", {}).get("5", 0), 
                     b_data.get("source_recall_at", {}).get("5", 0)),
    }
    
    metric_names = list(metrics.keys())
    a_values = [v[0] for v in metrics.values()]
    b_values = [v[1] for v in metrics.values()]
    
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    
    x = np.arange(len(metric_names))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, a_values, width, label='A: Vector-Only', color='#1f77b4', alpha=0.8)
    bars2 = ax.bar(x + width/2, b_values, width, label='B: Hybrid+Rerank', color='#ff7f0e', alpha=0.8)
    
    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax.set_title('RAG Performance Metrics (Natural Language Dataset)', 
                 fontsize=13, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(metric_names, fontsize=10)
    ax.set_ylim(0.7, 1.05)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{height:.3f}',
                   ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved figure: {output_path}")
    plt.close()


def main() -> int:
    """Generate all plots from reports."""
    # Natural dataset (more realistic)
    natural_report = Path("data/reports/rag_ab_report_natural_round8.json")
    if natural_report.exists():
        print(f"Generating plots from: {natural_report}")
        plot_recall_comparison(natural_report, Path("data/reports/fig_recall_natural_round8.png"))
        plot_metric_comparison(natural_report, Path("data/reports/fig_metrics_natural_round8.png"))
    else:
        print(f"Report not found: {natural_report}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
