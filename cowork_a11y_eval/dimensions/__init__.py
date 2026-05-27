from .base import Dimension, CaseResult, DimensionSummary
from .screenreader_format import ScreenreaderFormat
from .modality_awareness import ModalityAwareness
from .plain_language import PlainLanguage
from .refusal_parity import RefusalParity
from .aac_handling import AACHandling
from .tool_a11y_preference import ToolA11yPreference

ALL_DIMENSIONS: list[type[Dimension]] = [
    ScreenreaderFormat,
    ModalityAwareness,
    PlainLanguage,
    RefusalParity,
    AACHandling,
    ToolA11yPreference,
]

__all__ = [
    "Dimension",
    "CaseResult",
    "DimensionSummary",
    "ScreenreaderFormat",
    "ModalityAwareness",
    "PlainLanguage",
    "RefusalParity",
    "AACHandling",
    "ToolA11yPreference",
    "ALL_DIMENSIONS",
]
