import matplotlib.pyplot as plt


def apply():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150, "savefig.dpi": 300, "pdf.fonttype": 42})


def save(fig, filename):
    from pathlib import Path
    target = Path(filename)
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(target, bbox_inches="tight")
    plt.close(fig)
