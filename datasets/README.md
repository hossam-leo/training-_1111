# Dataset and evaluation scaffolds

This directory intentionally contains no real participant recordings and no fabricated accuracy results. The scripts create synthetic metadata and validate supplied annotations. Replace the synthetic fixtures with consented recordings or permissively licensed assets before claiming SRS evaluation.

Required external inputs:

- DR-1: at least 50 consented mock sessions across the SRS scenarios, lighting, webcam, and noise conditions.
- DR-2: at least 1,500 annotated images, including hard negatives and a 100-image overlap for inter-annotator agreement.
- DR-3: a documented 50-trial physical spoof kit.

Use `python datasets/generate_synthetic_scenarios.py --count 50` to generate clearly labeled metadata only. It does not create media and cannot support accuracy claims.
