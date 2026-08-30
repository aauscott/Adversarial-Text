"""Public API for generating and analyzing confusable text variants."""

from .deobfuscation import DeobfuscationChange, DeobfuscationResult, deobfuscate_text
from .generator import (
    DEFAULT_TRANSFORM_ORDER,
    PipelineConfig,
    apply_pipeline,
    generate_variants,
    resolve_transforms,
)
from .homoglyph_data import HOMOGLYPH_SETS
from .scoring import (
    AnalysisResult,
    detect_confusables,
    detect_invisible_spacing,
    suspicion_score,
    unicode_normalize,
)
from .transformations import (
    HOMOGLYPH_MAP,
    INVISIBLE_SPACING_CHARS,
    homoglyph_substitution,
    invisible_spacing_noise,
    leetspeak_transformation,
    random_character_noise,
    spacing_punctuation_noise,
)

__version__ = "0.1.0"

__all__ = [
    "AnalysisResult",
    "DEFAULT_TRANSFORM_ORDER",
    "DeobfuscationChange",
    "DeobfuscationResult",
    "HOMOGLYPH_MAP",
    "HOMOGLYPH_SETS",
    "INVISIBLE_SPACING_CHARS",
    "PipelineConfig",
    "apply_pipeline",
    "deobfuscate_text",
    "detect_confusables",
    "detect_invisible_spacing",
    "generate_variants",
    "homoglyph_substitution",
    "invisible_spacing_noise",
    "leetspeak_transformation",
    "random_character_noise",
    "resolve_transforms",
    "spacing_punctuation_noise",
    "suspicion_score",
    "unicode_normalize",
]
