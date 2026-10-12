# Actionable support in school AI assistants

Research materials for *Combining emotional recognition with actionable guidance in school AI assistants*.

The current release contains 60 constructed scenarios, 720 model replies, original human labels, and aggregate questionnaire counts for 27,396 respondents. The seven within-respondent comparisons cover 27,301 students, parents and teachers; 95 principals contribute contextual item frequencies.

## Reproduce

```bash
python -m pip install -r requirements.txt
python scripts/validate_release.py
python scripts/reproduce.py
```

The analysis uses stored replies and runs offline. It checks the reference results and manuscript tables. Two coding versions retain the independent labels for 144 replies and share 552 singly coded replies. The 24 calibration replies are excluded from analysis. Blank labels remain missing.

To redraw the figures with Times New Roman installed:

```bash
python scripts/plot_figures.py
```

On systems without that font, use `--font "DejaVu Serif"`. Numerical results are unchanged. Figure styling follows [figures4papers](https://github.com/ChenLiu-1996/figures4papers).

## Files

| Folder | Contents |
| --- | --- |
| `data/` | Reply texts, human labels, scenarios, prompt modules, codebook, survey item counts and joint counts |
| `scripts/` | Offline analysis, table checks and plotting |
| `results/reference/` | Checked statistical outputs |
| `results/tables/` | Source tables matching the manuscript |
| `figures/` | Five manuscript figures in PDF format |

See [TABLE_MAP.md](docs/TABLE_MAP.md) for Tables S1–S17 and variable definitions. Questionnaire counts preserve the original response options; concern items are not reverse scored. No individual questionnaire rows are included.

Version 2 corresponds to the current manuscript. Version 1 remains an archived earlier study.
