# Adversarial Text Lab

A toolkit for generating and analyzing adversarially perturbed text, with a focus on obfuscation techniques used in real-world scam and spam messages.

## Overview

Adversarial Text Lab is designed to simulate how malicious actors manipulate text to evade detection systems. It provides tools to:

- Generate obfuscated text variants (homoglyphs, leetspeak, spacing attacks)
- Analyze and score text for suspicious patterns
- Benchmark how robust classifiers are to adversarial inputs

This project focuses on **defensive research and robustness testing**, not operational misuse.

---

## Motivation

Modern text-based detection systems (spam filters, scam classifiers) often assume clean input. In reality, adversaries use:

- Unicode homoglyphs (e.g., `paypaI` vs `paypal`)
- Character substitutions (`fr33`, `cl!ck`)
- Random spacing and punctuation
- Obfuscated URLs

This project explores how these techniques degrade model performance—and how to detect them.

---

## Features

### Adversarial Text Generation
- Homoglyph substitution (Unicode confusables)
- Leetspeak transformations
- Character-level noise injection
- Spacing and punctuation perturbations

### Text Analysis
- Unicode normalization
- Confusable character detection
- Suspicion scoring
- Best-effort deobfuscation with candidate alternatives and a change audit

---

## Project Structure

adversarial-text-lab/
│
├── adversarial/            # core transformation functions
├── analysis/               # normalization + scoring
├── pipeline/               # composed variant generation
├── tests/
├── cli.py                  # command-line entry point
└── README.md

---

## Quick Start

Environment setup:

python3 -m venv .venv
source .venv/bin/activate

Command:

python cli.py --text "Your account has been suspended. Click here to verify."

Generate more variants:

python cli.py --text "your message" --variants 5 --seed 42

Run only specific transforms:

python cli.py --text "your message" --only homoglyph spacing_noise

Exclude specific transforms:

python cli.py --text "your message" --exclude random_noise

Set fixed probabilities:

python cli.py --text "your message" --prob 0.25 --homoglyph-prob 0.6

Sample probabilities from ranges (per variant):

python cli.py --text "your message" --prob 0.05:0.20 --homoglyph-prob 0.30:0.70 --variants 5 --seed 42

Recover a conservative best-effort reading:

python cli.py --text "Ρаypаl  l0g1n" --decode

Allow more speculative punctuation and spacing cleanup:

python cli.py --text "h.e_l-l!o" --decode --decode-level aggressive

Decoding reports the best candidate, alternative readings, input and residual
suspicion scores, recovery confidence, and an audit of every change. Recovery is
heuristic: random insertions, deletions, and swaps cannot always be reversed.

---

## Testing

python3 -m unittest discover -s tests -p "test_*.py"

---

## Roadmap (Post-MVP)

- URL obfuscation transforms
- Entropy/irregularity metrics
- Synthetic dataset generator
- Benchmark harness for classifiers

---

## Disclaimer

This project is intended for **research and defensive purposes only**.
