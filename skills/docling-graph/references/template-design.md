# Template Design

Docling Graph templates are Pydantic models that describe the graph you want from a document. Treat them as extraction contracts, not passive data containers.

## Model Shape

Use clear `BaseModel` classes with typed fields and descriptions:

```python
from pydantic import BaseModel, ConfigDict, Field

from docling_graph.utils import edge


class Organization(BaseModel):
    """A company, agency, nonprofit, or other legal organization."""

    model_config = ConfigDict(json_schema_extra={"graph_id_fields": ["name"]})

    name: str = Field(description="Canonical organization name as written in the document")
    jurisdiction: str | None = Field(default=None, description="Jurisdiction if stated")


class FilingGraph(BaseModel):
    """Graph extracted from one filing document."""

    model_config = ConfigDict(json_schema_extra={"graph_id_fields": ["accession_number"]})

    accession_number: str = Field(description="SEC accession number for the filing")
    issuer: Organization = Field(description="Primary issuer for the filing")
    counterparties: list[Organization] = Field(
        default_factory=list,
        description=edge("mentions", "Other organizations mentioned in the filing"),
    )
```

## Stable IDs

Every reusable entity should have stable ID fields. Good ID inputs are normalized names, official identifiers, accession numbers, dates, jurisdictions, and document-specific keys. Weak ID inputs are extraction order, page number alone, model-generated labels, or vague descriptions.

Use root-level IDs for document graphs and entity-level IDs for reusable nodes.

## Relationship Fields

Relationship fields should be typed as another model or a list of models. Avoid `dict`, `Any`, and untyped lists for graph-critical relationships.

Add relationship semantics when supported by the installed Docling Graph helper APIs. Use descriptions that explain evidence, direction, and expected target type.

## Contract Fit

### Direct-Friendly

Direct extraction works best when:

- The root model is compact.
- Relationship count is modest.
- Lists are shallow.
- Field descriptions are precise.
- The provider supports structured output for the full schema.

### Staged-Friendly

Staged extraction fits when:

- The graph has clear sections or entity groups.
- Nested lists would make direct extraction fragile.
- Cross-stage relationships can be expressed with stable IDs.
- The root model can merge stage outputs deterministically.

### Delta-Friendly

Delta extraction fits when:

- The source has repeated observations of the same entity.
- Relationships are scattered across sections.
- High-cardinality collections dominate.
- Entity resolution matters more than one-shot field filling.

Delta templates need especially strong stable IDs and resolver-friendly fields.

## Review Checklist

- Root graph model is obvious.
- Each extracted field has a useful description.
- Reusable entities have stable ID fields.
- Relationship fields are typed and directional.
- High-cardinality collections have a staged/delta plan.
- Optional fields are explicitly nullable or defaulted.
- No graph-critical fields use `Any`, `dict`, or untyped `list`.
- Template can be imported by the intended CLI/API path.
