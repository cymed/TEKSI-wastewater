# TEKSI Hooks Architecture Status

## Purpose

This document summarizes the current implementation state of the TEKSI Hooks framework and records architectural decisions made during development.

It serves as:

- project onboarding documentation;
- architecture reference;
- implementation roadmap;
- context snapshot for future AI-assisted development sessions.

The framework remains intentionally independent from TEKSI Wastewater and uses adapters to bridge into plugin-specific functionality.

---

# Guiding Principles

## Canonical identifiers first

All framework logic operates on canonical TWW identifiers.

```text
Source Model
        ↓
Canonical TWW Model
        ↓
Rights
Validation
Diff
Persistence
```

Rights, validation and diffing must not depend on source-model semantics.

---

## Strict layering

```text
Parser
    ↓
Parsed Models
    ↓
Resolver
    ↓
Resolved Models
    ↓
Capabilities
    ↓
Evaluators
    ↓
Services
    ↓
Adapters
```

Responsibilities:

| Layer | Purpose |
|---------|---------|
| Parser | Parse YAML / JSON |
| Resolver | Expand defaults, inheritance and configuration |
| Models | Domain contracts |
| Capabilities | Lookup services |
| Evaluators | Business decisions |
| Services | Workflow orchestration |
| Adapters | Integration with TEKSI/QGIS/runtime |

---

# Rights Framework

## Current Status

Implemented:

- Rights parser
- Rights resolver
- Rights capability
- Rights evaluator
- Provider capability
- Conditions capability
- Derived rights parser support
- Derived rights resolver support
- Derived rights capability
- Relation lookup abstraction

Covered by tests.

---

# Class inheritance

Still represented by:

```yaml
extends:
```

Example:

```yaml
- id: maintenance
  extends: maintenance_event
```

Meaning:

```text
IS-A relationship
```

Inheritance remains conceptually separate from rights derivation.

---

# Rights derivation

Rights derivation models:

```text
RELATED-TO relationship
```

and is intentionally independent from inheritance.

---

## Local FK

```yaml
derive_rights_from:
  - class: wastewater_structure
    local_attribute: fk_wastewater_structure
```

Meaning:

```text
local.fk_wastewater_structure
    =
wastewater_structure.obj_id
```

---

## Reverse FK

```yaml
derive_rights_from:
  - class: reach
    remote_attribute: fk_reach_point_from

  - class: reach
    remote_attribute: fk_reach_point_to
```

Meaning:

```text
reach_point.obj_id
    =
reach.fk_reach_point_from

reach_point.obj_id
    =
reach.fk_reach_point_to
```

---

## Explicit join

```yaml
derive_rights_from:
  - class: foo
    local_attribute: fk_baz
    remote_attribute: fk_bar
```

Meaning:

```text
local.fk_baz
    =
foo.fk_bar
```

---

# Derived Rights Runtime Architecture

## Parsed model

```python
DerivedRights
```

Stores:

```python
class_id
local_attribute
remote_attribute
```

This remains a configuration model.

---

## Resolved model

```python
ResolvedDerivedRights
```

Stores:

```python
local_objects
remote_objects
```

using:

```python
CanonicalObjectIdentity
```

instances.

Meaning:

```text
Parsed:
    How to derive rights

Resolved:
    What objects participate
```

---

# Canonical Object Model

A new canonical object contract has been introduced.

File:

```text
models/canonical_object.py
```

---

## CanonicalObjectIdentity

Represents a unique object reference.

```python
CanonicalObjectIdentity
```

Contains:

```python
class_id
attributes
```

Example:

```python
CanonicalObjectIdentity(
    class_id="reach",
    attributes={
        "obj_id": "...",
    },
)
```

---

## CanonicalObject

Represents a current object.

```python
CanonicalObject
```

Contains:

```python
identity
values
last_modification
```

This model is intended to become the common contract used by:

- relation lookup;
- diff snapshots;
- persistence;
- validation;
- future APIs.

---

# Relation Lookup Capability

New capability:

```python
RelationLookupCapability
```

Responsibilities:

```python
current_object(...)
resolve_derived_rights(...)
```

Purpose:

```text
CanonicalObjectIdentity
        ↓
Current object lookup

CanonicalObjectIdentity
        ↓
ResolvedDerivedRights
```

This capability acts as the bridge between:

```text
RightsEvaluator
SnapshotValidationEvaluator
Future validation
Future persistence
```

and actual data access.

No implementation exists yet.

Only the abstraction exists.

---

# Effects Framework

## Current models

```python
EffectDocument
EffectSource

Effect
UpdateAttributeEffect
EnforceExistsEffect
EnforceNotExistsEffect
```

Current vocabulary:

```python
EffectKind.UPDATE_ATTRIBUTE
EffectKind.ENFORCE_EXISTS
EffectKind.ENFORCE_NOT_EXISTS
```

---

## Effect identities

Effects now use:

```python
CanonicalObjectIdentity
```

instead of ad-hoc identity mappings.

Example:

```python
UpdateAttributeEffect(
    identity=CanonicalObjectIdentity(...),
)
```

---

## EffectDocument

Current contract:

```python
EffectDocument
```

contains:

```python
version
created_at
source
effects
```

`created_at` is automatically assigned through the model.

---

## EffectDocumentValidator

Implemented:

```python
EffectDocumentValidator
```

Validation currently covers:

```text
Document version
Identity presence
Identity class
Identity attributes
Attribute identifiers
```

Unit tests exist.

---

# Diff Snapshot Framework

Significant progress has been made.

---

## SnapshotMetadata

Stores:

```python
created_at
source_model
source_class_id
source_object_id
```

---

## SnapshotObject

Stores:

```python
identity
last_modification
```

where:

```python
identity
```

is:

```python
CanonicalObjectIdentity
```

---

## SnapshotState

Introduced states:

```python
CURRENT
MODIFIED
DELETED
```

These belong to the snapshot domain itself rather than validation.

---

## SnapshotValidationFinding

Stores:

```python
identity
state
```

---

## DiffSnapshot

Current structure:

```python
DiffSnapshot
├── metadata
├── objects
└── effects
```

Purpose:

```text
Immutable diff review contract
```

---

# Diff Snapshot Builder

Implemented:

```python
DiffSnapshotBuilder
```

Responsibility:

```text
EffectDocument
        ↓
DiffSnapshot
```

Behavior:

```text
Groups effects by canonical object
Creates snapshot objects
Copies metadata
Carries effects forward
```

Unit tests exist.

---

# Snapshot Validation

## Evaluator

Introduced:

```python
SnapshotValidationEvaluator
```

Current status:

```text
Contract defined
Implementation started
Tests introduced
```

Uses:

```python
RelationLookupCapability
```

---

## Business goal

A snapshot may be reviewed days after generation.

Validation therefore compares:

```text
snapshot.last_modification
        ==
current.last_modification
```

and reports:

```python
SnapshotState.MODIFIED
```

or:

```python
SnapshotState.DELETED
```

when necessary.

---

# Mapping Framework

Implemented:

```python
ModelMappingCapability
DictionaryMappingCapability
```

---

## Naming cleanup

Dictionary mapping API now follows:

```python
class_mapping_for_ili(...)
attribute_mapping_for_ili(...)
value_mapping_for_ili(...)
```

to better reflect semantics.

---

# Adapter Layer

Implemented:

```python
TwwInterlisServiceAdapter
TwwRelationContextProvider
```

Unit tests added.

Additional CI fixes are being merged separately.

---

# Validation Framework

## Current state

Implemented:

```python
TransitionValidation
StateTransitionRule
ValidationResolver
```

---

## Bilateral transitions

Resolver expands:

```python
bilateral=True
```

into:

```text
A → B
B → A
```

during runtime resolution.

Evaluators therefore consume an explicit transition graph.

---

# Test Architecture

The test suite has been reorganized around framework layers.

```text
tests/

parser/
resolver/
capabilities/
evaluators/
services/
interlis/
adapters/
```

This structure now mirrors the production architecture.

---

# Current Major Contracts

The following contracts are now considered relatively stable:

```python
CanonicalObjectIdentity
CanonicalObject

DerivedRights
ResolvedDerivedRights

EffectDocument
Effect

DiffSnapshot
SnapshotObject
SnapshotState

RelationLookupCapability
```

Future implementation should build on these rather than introducing alternative representations.

---

# To-Do

## Rights

- Complete runtime derived-right traversal using RelationLookupCapability.
- Re-enable full derived-right authorization tests.
- Implement rights_from_subclass evaluation.
- Add inheritance edge-case tests.
- Add wildcard expansion tests.

---

## Relation Lookup

- Implement SQL-backed RelationLookupCapability.
- Implement adapter-backed relation lookup.
- Define lookup strategy for subclass traversal.
- Add relation lookup capability tests.

---

## Validation

- Complete SnapshotValidationEvaluator implementation.
- Implement ValidationEvaluator.
- Implement AttributeValidation execution.
- Implement TransitionValidation execution.
- Implement transitive transition evaluation.

---

## Diff Framework

- Complete EffectDocument → DiffSnapshot workflow.
- Add snapshot refresh mechanism.
- Detect relation graph changes after snapshot creation.
- Detect newly inserted related objects.
- Detect deleted related objects.
- Add conflict reporting.

---

## Snapshot Lifecycle

- Implement stale snapshot detection.
- Define snapshot refresh strategy.
- Define snapshot invalidation policy.
- Add snapshot revalidation workflow.

---

## Effects

- Define JSON schema.
- Add serialization helpers.
- Add deserialization helpers.
- Add persistence interfaces.

---

## Mapping

- Implement attribute value mappings.
- Implement dictionary value mappings.
- Implement mapping tests for values.
- Implement AG64 projection functions.
- Implement AG96 projection functions.
- Finalize JSONB effect contract documentation.

---

## Change Loading

- Design canonical Change model.
- Decide relationship between Change and EffectDocument.
- Implement ChangeLoader.
- Implement geometry comparison.
- Implement foreign-key comparison.
- Implement value-list comparison.
- Implement transformed attribute comparison.
- Integrate AGXX projection functions.

---

## Persistence

- Define persistence capability.
- Implement update_attribute persistence.
- Implement enforce_exists persistence.
- Implement enforce_not_exists persistence.
- Add persistence tests.

---

## QGIS Diff Viewer

- Define viewer data contract.
- Build object