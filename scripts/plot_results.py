"""Create publication-quality charts from reproduced summary tables."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results/reproduced'
FIGURES = ROOT / 'figures'
BLUE, ORANGE, INK = '#287A9B', '#C56B37', '#243746'


def style():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False,
        'axes.edgecolor': '#B9C4CD', 'axes.labelcolor': INK, 'text.color': INK,
        'xtick.color': '#516371', 'ytick.color': INK, 'savefig.facecolor': 'white',
        'svg.fonttype': 'none', 'pdf.fonttype': 42})


def save(fig, name):
    for ext in ['png', 'svg', 'pdf']:
        fig.savefig(FIGURES / f'{name}.{ext}', dpi=200, bbox_inches='tight')
    plt.close(fig)


def responsibility():
    data = pd.read_csv(RESULTS / 'content_prevalence_percent.csv').set_index('condition')
    features = ['responsible_actor_attribution', 'institutional_stake_recognition', 'procedural_remedy',
                'emotional_validation', 'unsupported_authority_claim', 'over_escalation']
    labels = ['Responsible adult named', 'Institutional stakes recognised', 'Procedural remedy offered',
              'Emotion acknowledged', 'Unsupported authority claim', 'Over-escalation']
    fig, ax = plt.subplots(figsize=(11.6, 5.7))
    fig.subplots_adjust(left=.32, right=.91, top=.79, bottom=.19)
    y = np.arange(6)[::-1]
    for idx, field in enumerate(features):
        a, b = data.loc['default', field], data.loc['principal_prompt', field]
        ax.plot([a, b], [y[idx], y[idx]], color='#CFD8DD', linewidth=3, zorder=1)
        ax.scatter(a, y[idx], s=90, color=BLUE, zorder=3)
        ax.scatter(b, y[idx], s=90, color=ORANGE, zorder=3)
        ax.annotate(f'{a:.1f}%', (a, y[idx]), xytext=(0, -19), textcoords='offset points', ha='center', color=BLUE, fontsize=10)
        ax.annotate(f'{b:.1f}%', (b, y[idx]), xytext=(0, 11), textcoords='offset points', ha='center', color=ORANGE, fontsize=10)
    ax.set_yticks(y, labels)
    ax.tick_params(axis='y', length=0, pad=15)
    ax.set_xlim(-5, 105)
    ax.set_ylim(-.65, 5.75)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    ax.set_xlabel('Share of coded responses', labelpad=11)
    ax.grid(axis='x', color='#EBEFF2')
    ax.set_axisbelow(True)
    ax.axhline(1.5, color='#D8E0E6', linewidth=.8, linestyle='--')
    fig.text(.045, .96, 'School advice: procedures, support and authority', fontsize=19, weight='bold')
    fig.text(.045, .902, 'Default', color=BLUE, fontsize=12, weight='bold')
    fig.text(.17, .902, 'Principal identity + governance instructions', color=ORANGE, fontsize=12, weight='bold')
    fig.text(.045, .035, '180 coded replies per condition • 60 matched scenarios • 3 generators\nObserved content prevalence; the instruction package combines role identity and task priorities.', fontsize=9, color='#516371')
    save(fig, 'responsibility_content')


def voice():
    data = pd.read_csv(RESULTS / 'h3_voice_shares.csv')
    roles = ['student', 'parent', 'teacher', 'principal']
    colors = ['#A9BAC8', '#6C9D89', BLUE, ORANGE]
    labels = ['Default', 'Principal instructions', 'Teacher-speaker task', 'Principal-speaker task', 'Frontier default']
    fig, ax = plt.subplots(figsize=(11.6, 5.4))
    fig.subplots_adjust(left=.25, right=.96, top=.77, bottom=.20)
    y = np.arange(len(data))[::-1]
    left = np.zeros(len(data))
    for role, color in zip(roles, colors):
        values = data[f'{role}_percent'].to_numpy()
        ax.barh(y, values, left=left, height=.58, color=color, label=role.title(), edgecolor='white', linewidth=.7)
        for idx, value in enumerate(values):
            if value >= 5:
                ax.text(left[idx] + value / 2, y[idx], f'{value:.1f}', color='white' if role in ['teacher', 'principal'] else INK, ha='center', va='center', fontsize=10, weight='bold')
        left += values
    ax.set_yticks(y, [f'{label}\n(n = {n:,})' for label, n in zip(labels, data.n)])
    ax.tick_params(axis='y', length=0, pad=14)
    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    ax.set_xlabel('Dominant predicted voice class', labelpad=10)
    ax.legend(ncol=4, loc='lower left', bbox_to_anchor=(0, 1.03), frameon=False)
    fig.text(.045, .95, 'How predicted voice changes with framing', fontsize=19, weight='bold')
    fig.text(.045, .035, 'MiniLM–SetFit classification • 1,800 replies in total\nDefault / instruction / frontier conditions cover 60 scenarios; speaker-task conditions cover 10.', fontsize=9, color='#516371')
    save(fig, 'voice_distributions')


if __name__ == '__main__':
    FIGURES.mkdir(parents=True, exist_ok=True)
    style()
    responsibility()
    voice()
    print(f'Created two figures in PNG, SVG and PDF: {FIGURES}')
