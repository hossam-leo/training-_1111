# Detector dataset card

## Intended use

The dataset supports research evaluation of prohibited-object detection in consented mock-exam environments. It must not be used to infer candidate intent or make unattended decisions.

## Annotation format

Each JSON row contains `image`, `split` (`train`, `val`, or `test`), and `labels`. A label contains the class name and bounding-box coordinates in the supplied annotation implementation. Hard negatives must include hands near face, water bottles, pens, glasses cases, TV remotes, and calculators.

## Required scale

The SRS requires at least 1,500 annotated images, a hard-negative set, and a 100-image overlap for inter-annotator agreement. The repository does not include those assets. `generate_synthetic_scenarios.py` creates metadata only and cannot satisfy this requirement.

## Evaluation

`evaluate_detector.py` validates manifests and reports counts. Precision, recall, F1, confusion matrices, and baseline comparisons must be produced only after an actual detector is run against supplied labeled images.
