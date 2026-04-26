# Template Design

## Contents

1. Purpose
2. Template Checklist
3. Entity vs Component
4. Stable IDs
5. Relationships and Edges
6. Field Guidance
7. Validation
8. Review Output

## Purpose

Docling Graph templates are Pydantic models that define both extraction shape and graph shape. A good template gives the model concrete fields to extract, validates the result, and makes graph nodes and edges predictable.

Use this reference in **Template** mode.

## Template Checklist

Before writing commands, verify:

| Check | Why it matters |
|---|---|
| Root model exists | Pipeline needs a clear extraction target |
| Domain classes have docstrings | LLMs use schema text as extraction guidance |
| Important fields have `Field(description=...)` | Field descriptions reduce ambiguous extraction |
| Entities have stable identity | Prevents duplicate nodes across documents |
| Components are marked or treated as nested value objects | Avoids unnecessary graph nodes |
| Relationship fields are explicit | Edges should encode semantics, not accidental nesting |
| Validators enforce domain invariants | Bad data should fail near extraction |

## Entity vs Component

Use an **entity** when the object has independent identity and may appear in multiple places:

| Entity signals | Examples |
|---|---|
| Has a name, identifier, account number, DOI, CUSIP, contract ID, or date pair | Organization, Person, Instrument, Contract, ChemicalCompound |
| Should deduplicate across pages or documents | Vendor, Customer, ResearchPaper |
| Needs direct graph traversal | Claim, Obligation, Reaction, Measurement |

Use a **component** when the object only describes another object:

| Component signals | Examples |
|---|---|
| No stable identity outside parent | Address, MoneyAmount, DateRange |
| Usually embedded as structured properties | ContactInfo, Dimensions |
| Duplicating it as a node adds noise | Formatting, Notes |

If uncertain, start as a component. Promote to entity when users need cross-document linking or graph traversal.

## Stable IDs

Stable IDs are the main duplicate-control mechanism.

Guidelines:

1. Prefer real identifiers over generated IDs.
2. Use a small set of fields that are stable across documents.
3. Avoid volatile fields such as extraction timestamp, page number, or display-only labels.
4. For people, combine multiple fields if available: name plus birth date, affiliation, or role.
5. For documents, use document number, DOI, URL, accession number, or title plus date.

Common examples:

```python
from pydantic import BaseModel, ConfigDict, Field

class Organization(BaseModel):
    model_config = ConfigDict(is_entity=True, graph_id_fields=["name"])
    name: str = Field(description="Legal organization name")

class Filing(BaseModel):
    model_config = ConfigDict(is_entity=True, graph_id_fields=["accession_number"])
    accession_number: str = Field(description="SEC accession number")
```

## Relationships and Edges

Use plain nested fields when field names already make the relationship clear. Use explicit edge labels when graph semantics matter:

```python
from pydantic import BaseModel, Field
from docling_graph.utils import edge

class Person(BaseModel):
    name: str = Field(description="Person name")

class Organization(BaseModel):
    name: str = Field(description="Organization name")
    employees: list[Person] = edge("EMPLOYS", description="People employed by this organization")
```

Edge-label rules:

1. Use verb phrases or domain relationship names.
2. Keep labels stable across template revisions.
3. Avoid generic labels such as `HAS` unless the domain genuinely lacks semantics.
4. Use one edge field per relationship meaning.

## Field Guidance

Field descriptions should tell the extractor what to capture and what not to capture.

Good:

```python
total_due: str = Field(
    description="Final amount due, including currency symbol if present. Do not use subtotal."
)
```

Weak:

```python
total_due: str = Field(description="Total")
```

Prefer `examples=[...]` for ambiguous formats. Use enums or literals for constrained values.

## Validation

Use validators when bad values are common or expensive downstream:

| Invariant | Example |
|---|---|
| Required identifier shape | invoice number, DOI, accession number |
| Numeric or currency format | amount, rate, concentration |
| Date ordering | effective date before expiry date |
| Controlled values | jurisdiction, instrument type, reaction role |

Do not overfit validation before sample documents are reviewed. Start with high-value invariants.

## Review Output

A template review should include:

1. Template purpose and root model.
2. Entity/component table.
3. Stable ID choices and risks.
4. Edge labels and relationship meaning.
5. Field descriptions that need strengthening.
6. Validation recommendations.
7. Small example command or API config that uses the template.
