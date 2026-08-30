# Adversarial Text

A Python library and command-line tool for generating, analyzing, and reversing
confusable text variants used in defensive model training and robustness tests.

## Features

- Unicode homoglyph substitution across configurable scripts and styles
- Leetspeak, visible spacing, invisible spacing, and random character noise
- Deterministic multi-variant generation with seeded randomness
- Optional preservation of existing digits during homoglyph substitution
- Unicode normalization, confusable detection, and heuristic suspicion scoring
- Best-effort deobfuscation with alternatives and an auditable change list

This project is intended for defensive research and robustness testing.

## Installation

```bash
git clone https://github.com/aauscott/Adversarial-Text.git
cd Adversarial-Text
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

The editable installation provides the `adversarial-text` command and the
`adversarial_text` Python package.

## Command-line usage

Generate variants:

```bash
adversarial-text --text "Your account has been suspended" --variants 5 --seed 42
```

Run selected transforms with subtle probabilities:

```bash
adversarial-text \
  --text "Example phrase 12345" \
  --only homoglyph invisible_spacing leetspeak \
  --homoglyph-prob 0.05 \
  --invisible-prob 0.01 \
  --leetspeak-prob 0.01 \
  --preserve-digits \
  --variants 5 \
  --seed 42
```

Restrict homoglyph replacements to selected scripts:

```bash
adversarial-text \
  --text "your message" \
  --only homoglyph \
  --homoglyph-include greek cyrillic
```

Exclude compatibility or miscellaneous characters:

```bash
adversarial-text \
  --text "your message" \
  --homoglyph-exclude fullwidth mathematical other
```

Decode a confusable phrase:

```bash
adversarial-text --text "Ρаypаl  l0g1n" --decode
```

The module entry point is also available:

```bash
python -m adversarial_text --text "your message"
```

## Python API

```python
from adversarial_text import PipelineConfig, generate_variants

config = PipelineConfig(
    homoglyph_probability=0.05,
    leetspeak_probability=0.01,
    invisible_spacing_probability=0.01,
    spacing_noise_probability=0.0,
    random_noise_probability=0.0,
    preserve_digits=True,
)

variants = generate_variants(
    "Example training phrase 12345",
    num_variants=20,
    config=config,
    seed=42,
)
```

The main generation, transformation, scoring, and deobfuscation helpers are
exported directly from `adversarial_text`.

## Homoglyph controls

Available `--homoglyph-include` and `--homoglyph-exclude` values are `latin`,
`greek`, `cyrillic`, `armenian`, `cherokee`, `coptic`, `canadian`, `fullwidth`,
`mathematical`, and `other`. Exclusions take precedence over inclusions.

`--preserve-digits` prevents existing digits from being changed by homoglyph
substitution. It does not prevent leetspeak from converting letters into digits,
and it does not constrain random character noise.

## Homoglyph data

The expanded map is built from
`src/adversarial_text/data/codebox_ascii_homoglyphs.txt`, an adapted,
ASCII-anchored subset of the MIT-licensed
[Codebox Homoglyph character data](https://github.com/codebox/homoglyph/blob/master/raw_data/chars.txt).
The checked-in data keeps generation deterministic and avoids a runtime network
dependency. Project-curated characters are merged before the derived groups,
then generation selects uniformly from the complete candidate list.

See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for attribution.

## Scoring

The suspicion score is a bounded heuristic for comparing transformed variants;
it is not a maliciousness probability. Legitimate digits and punctuation can
increase the score because they may resemble leetspeak or spacing noise.

## Project structure

```text
Adversarial-Text/
├── src/adversarial_text/      # installable library and CLI
├── tests/                     # focused unit tests
├── LICENSE                    # project MIT license
├── THIRD_PARTY_NOTICES.md     # third-party attribution
├── pyproject.toml             # package metadata
└── README.md
```

## Testing

After installing the project in editable mode:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## License

Adversarial Text is available under the [MIT License](LICENSE). The adapted
Codebox Homoglyph data retains its original MIT notice.
