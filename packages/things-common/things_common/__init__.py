"""Shared security primitives for the Things++ MCP stack.

This package is deliberately not an MCP server.  All Things++ backends import
the same implementation so writes cannot escape the cross-process lock or use
incompatible confirmation receipts.
"""

from .canonical import canonical_bytes, canonical_schema_sha256, canonical_sha256
from .integrity import (
    ArtifactVerification,
    RecordVerification,
    verify_artifact,
    verify_record_tree,
)
from .mutation import (
    MutationAmbiguousError,
    MutationBusyError,
    MutationCoordinator,
    MutationError,
    MutationExecution,
    MutationIntent,
    MutationPhase,
    MutationPreview,
    MutationReceiptError,
    MutationRecovery,
    MutationStateError,
)
from .redaction import content_free_event, redact_text, redact_value
from .security import (
    AdvisoryMutationLock,
    LockCancelledError,
    LockTimeoutError,
    SecureRuntimePaths,
    SecurityViolation,
    ensure_secure_runtime_root,
    secure_file_descriptor,
    secure_read_bytes,
    secure_read_from_descriptor,
    secure_write_bytes,
    secure_write_to_descriptor,
)

__all__ = [
    "AdvisoryMutationLock",
    "ArtifactVerification",
    "LockCancelledError",
    "LockTimeoutError",
    "MutationAmbiguousError",
    "MutationBusyError",
    "MutationCoordinator",
    "MutationError",
    "MutationExecution",
    "MutationIntent",
    "MutationPhase",
    "MutationPreview",
    "MutationReceiptError",
    "MutationRecovery",
    "MutationStateError",
    "RecordVerification",
    "SecureRuntimePaths",
    "SecurityViolation",
    "canonical_bytes",
    "canonical_schema_sha256",
    "canonical_sha256",
    "content_free_event",
    "ensure_secure_runtime_root",
    "redact_text",
    "redact_value",
    "secure_file_descriptor",
    "secure_read_bytes",
    "secure_read_from_descriptor",
    "secure_write_bytes",
    "secure_write_to_descriptor",
    "verify_artifact",
    "verify_record_tree",
]
