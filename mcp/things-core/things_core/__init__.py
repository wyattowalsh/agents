"""Audited, typed adapter around ``mcp-server-things==1.9.0``."""

from .adapter import CoreBackend, ThingsCoreAdapter
from .contracts import (
    MAX_BATCH_ITEMS,
    CoreContractError,
    ToolContract,
    adapted_input_schema,
    adapted_output_schema,
    load_contracts,
    validate_arguments,
    validate_frozen_contract,
)
from .models import CoreToolResult
from .provenance import (
    DistributionEvidence,
    ProvenanceError,
    verify_distribution_artifacts,
    verify_installed_distribution,
)

__all__ = [
    "MAX_BATCH_ITEMS",
    "CoreBackend",
    "CoreContractError",
    "CoreToolResult",
    "DistributionEvidence",
    "ProvenanceError",
    "ThingsCoreAdapter",
    "ToolContract",
    "adapted_input_schema",
    "adapted_output_schema",
    "load_contracts",
    "validate_arguments",
    "validate_frozen_contract",
    "verify_distribution_artifacts",
    "verify_installed_distribution",
]
