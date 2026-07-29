# TEKSI Hooks Architecture Status

## Purpose

This document summarizes the current implementation state of the TEKSI Hooks framework and records architectural decisions made during development.

It serves as:

- project onboarding documentation
- architecture reference
- implementation roadmap
- context snapshot for future development sessions

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
````

Rights, validation, diffing and persistence should not depend on source-model semantics.

***

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

| Layer        | Purpose                                        |
| ------------ | ---------------------------------------------- |
| Parser       | Parse YAML / JSON                              |
| Resolver     | Expand defaults, inheritance and configuration |
| Models       | Domain contracts                               |
| Capabilities | Lookup and execution services                  |
| Evaluators   | Business decisions                             |
| Services     | Workflow orchestration                         |
| Adapters     | Integration with TEKSI/QGIS/runtime            |

***

# Major Architectural Decisions

## Effects describe desired state

Effects do not directly mean insert, update or delete.

Instead:

```text
EffectDocument
        +
Current database state
        ↓
ChangeBuilder
        ↓
ChangeOperation.INSERT / UPDATE / DELETE
```

Example:

```python
UpdateAttributeEffect(
    identity=CanonicalObjectIdentity(
        class_id="wastewater_structure",
        attributes={
            "obj_id": "ch987654WS123456",
        },
    ),
    tww_attribute_id="status",
    value="operational",
)
```

can contribute to either an update or an insert.

The decision depends on whether the current object exists.

***

## ChangeBuilder stays inheritance-unaware

TWW stores superclass and subclass information in separate tables, for example:

```text
wastewater_networkelement.obj_id = reach.obj_id
wastewater_networkelement.obj_id = wastewater_node.obj_id
```

`ChangeBuilder` should not know about this physical inheritance structure.

Inheritance-aware projection belongs upstream, where source data is translated into effects for the correct canonical table/class.

Example:

```text
source reach object
        ↓
UpdateAttributeEffect for wastewater_networkelement
UpdateAttributeEffect for reach
```

`ChangeBuilder` only groups and applies effects per canonical identity.

***

## Database integrity checks stay plugin-specific

Subclass/superclass count consistency is a TEKSI Wastewater physical schema concern.

The current `TwwIntegrityChecker` should remain a standalone plugin utility for now.

Future integration should happen through a thin adapter:

```text
TwwIntegrityChecker
        ↓
TwwIntegrityCheckerAdapter
        ↓
ValidationFinding
```

The core framework should not know about TEKSI Wastewater physical table inheritance.

***

# Canonical Object Model

File:

```text
models/canonical_object.py
```

## CanonicalObjectIdentity

Represents a canonical object reference.

```python
CanonicalObjectIdentity(
    class_id="reach",
    attributes={
        "obj_id": "...",
    },
)
```

Contains:

```python
class_id
attributes
```

The `attributes` mapping represents object identity attributes, usually `obj_id`.

## CanonicalObject

Represents a loaded canonical object.

Contains:

```python
identity
values
last_modification
```

Used by:

* relation lookup
* snapshot validation
* change building
* future persistence
* future repository/adapters

***

# Rights Framework

## Current Status

Implemented:

* Rights parser
* Rights resolver
* `ResolvedRights`
* `RightsCapability`
* `DerivedRightsCapability`
* `SubclassRightsCapability`
* `ResolvedProviderCapability`
* `ConditionsCapability`
* `RightsEvaluator`
* Derived-right configuration parsing
* Derived-right configuration resolution
* Subclass-right configuration resolution
* Runtime relation lookup abstraction
* In-memory relation lookup implementation

Most rights tests are in place. The remaining active work is recursive derived-right and subclass-right traversal.

***

# Resolved Rights

The resolver now returns a single aggregate:

```python
ResolvedRights
```

Containing:

```python
classes
derived_rights
subclass_rights
allow_transitive_transitions
```

The resolver method for derived-right configuration is named:

```python
resolve_derived_rights_config()
```

This makes the layer distinction explicit:

```text
RightsResolver.resolve_derived_rights_config()
    = configuration resolution

RightsEvaluator._resolve_derived_rights()
    = runtime object graph resolution
```

***

# Class Inheritance

Class inheritance is still represented by:

```yaml
extends:
```

Example:

```yaml
- id: reach
  extends: wastewater_networkelement
```

Meaning:

```text
IS-A relationship
```

Inheritance remains conceptually separate from rights derivation.

A subclass may inherit resolved class definitions, but physical superclass/subclass table synchronization remains a plugin integrity concern.

***

# Rights Derivation

Rights derivation models:

```text
RELATED-TO relationship
```

It is intentionally independent from class inheritance.

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

## Explicit Join

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

***

# Derived Rights Runtime Architecture

## Configuration model

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

## Runtime model

```python
CanonicalDerivedRights
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

The field name `remote_objects` is still used in the model, even though newer relation-lookup wording prefers `related_objects`.

Meaning:

```text
DerivedRights
    = how rights may be derived

CanonicalDerivedRights
    = which canonical objects participated at runtime
```

***

# Recursive Rights Evaluation

The intended runtime update flow is:

```text
can_update(class_id, context)
        ↓
direct update rules
        ↓
derived rights
        ↓
subclass rights
```

Derived rights may themselves require further rights derivation.

Example:

```text
reach_point
    derives rights from reach
        reach
            extends wastewater_networkelement
            derives rights from wastewater_structure
                wastewater_structure
                    grants update rights
```

This means the evaluator should be able to walk:

```text
reach_point
    → reach
    → wastewater_structure
```

Current work:

* make `can_update()` delegate to a recursive private helper
* prevent cycles through a `visited` mechanism
* make subclass rights delegate through the same recursive helper
* keep relation lookup lookup-only

***

# Relation Lookup Capability

File:

```text
capabilities/relation_lookup.py
```

## RelationLookupCapability

Lookup-only abstraction.

Responsibilities:

```python
canonical_objects(...)
current_object(...)
```

Non-responsibilities:

```text
rights evaluation
derived-right orchestration
authorization decisions
```

`RightsEvaluator` interprets `DerivedRights` and calls:

```python
relation_lookup.canonical_objects(...)
```

## canonical\_objects

Conceptually evaluates:

```text
local.<local_attribute>
    =
related.<related_attribute>
```

Signature concept:

```python
canonical_objects(
    local_class_id,
    related_class_id,
    local_attribute,
    related_attribute,
    value,
)
```

Returns:

```python
Sequence[CanonicalObjectIdentity]
```

## current\_object

Loads the current object:

```text
CanonicalObjectIdentity
        ↓
CanonicalObject | None
```

Used by:

* snapshot validation
* recursive derived-right evaluation
* future persistence/repository code

## InMemoryRelationLookupCapability

Concrete in-memory implementation.

Lives in production framework code, not tests-only.

Used for:

* unit tests
* small offline scenarios
* examples
* debugging

Production runtime should later use a SQL-backed or plugin-adapter-backed implementation.

***

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

## Effect identities

Effects use:

```python
CanonicalObjectIdentity
```

Example:

```python
UpdateAttributeEffect(
    identity=CanonicalObjectIdentity(...),
    tww_attribute_id="status",
    value="operational",
)
```

## Effect JSON contract

The JSON contract now uses canonical identity directly.

```json
{
  "version": 1,
  "source": {
    "model": "agxx",
    "class_id": "GepKnoten",
    "object_id": "ch123456AG987654"
  },
  "effects": [
    {
      "kind": "update_attribute",
      "identity": {
        "class_id": "agxx_wastewater_node",
        "attributes": {
          "fk_wastewater_node": "ch123456AG987654"
        }
      },
      "tww_attribute_id": "ag64_function",
      "value": 1234
    }
  ]
}
```

The old JSON shape using `tww_class_id` and `tww_identity` has been dropped.

## EffectDocument

Current contract:

```python
EffectDocument
```

Contains:

```python
version
created_at
source
effects
```

`created_at` is automatically assigned by the model.

## EffectDocumentValidator

Implemented.

Returns:

```python
tuple[ValidationFinding, ...]
```

Also supports:

```python
validate_or_raise()
```

which raises:

```python
EffectValidationError
```

Validation currently covers:

```text
document version
identity presence
identity class
identity attributes
attribute identifiers
unsupported effect types
contradicting effects
```

Contradicting combinations:

| Combination                                    | Status  |
| ---------------------------------------------- | ------- |
| EnforceExistsEffect + UpdateAttributeEffect    | allowed |
| EnforceExistsEffect + EnforceNotExistsEffect   | invalid |
| UpdateAttributeEffect + EnforceNotExistsEffect | invalid |

***

# Change Framework

## Change

Existing row-level model:

```python
Change
```

Contains:

```python
table_name
object_id
operation
old_values
new_values
changed_attributes
```

`changed_attributes` derives attribute-level diffs from `old_values` and `new_values`.

## ChangeBuilder

Replaces the old `ChangeLoader` direction.

Responsibility:

```text
current CanonicalObject | None
+
effects for one identity
        ↓
Change
```

Current behavior:

* `current_object is None` produces `ChangeOperation.INSERT`
* `current_object exists` produces `ChangeOperation.UPDATE`
* multiple `UpdateAttributeEffect`s aggregate into one row-level `Change`
* unsupported effect types still raise `NotImplementedError`

`ChangeBuilder` does not know about TWW inheritance.

***

# Validation Framework

## Shared finding model

Base concepts now exist:

```python
Severity
Finding
ValidationFinding
```

Severity values:

```python
info
warning
error
```

Framework-specific exceptions inherit from:

```python
TwwHookError
```

Current specific errors include:

```python
ValidationError
EffectValidationError
RightsEvaluationError
SnapshotValidationError
```

## AttributeValidation

Validation rules now support operation scoping.

Example YAML:

```yaml
defaults:
  validation_rules:
    last_modification:
      rules:
        - id: newer_than_existing
          level: info

    fk_provider:
      rules:
        - id: equals_context_value
          context_value: provider_oid
          level: error
          operations:
            - insert

    fk_dataowner:
      rules:
        - id: equals_context_value
          context_value: dataowner_oid
          level: error
          operations:
            - insert
```

This replaces the old unintended global create ownership default.

Important distinction:

```text
create_rules / update_rules / delete_rules
    = authorization

validation_rules
    = value correctness
```

So `fk_provider` and `fk_dataowner` are validated on insert, but they do not automatically become update/delete authorization rules.

## ValidationRegistry

Implemented validators:

```text
newer_than_existing
cannot_decrease
equals_context_value
```

`equals_context_value` compares:

```text
new_value
    =
context_values[validation.context_value]
```

Example:

```yaml
fk_provider:
  rules:
    - id: equals_context_value
      context_value: provider_oid
      level: error
      operations:
        - insert
```

## ValidationEvaluator

Implemented:

```python
validate_attribute()
validate_transition()
validate_change()
```

Current behavior:

* attribute validations are filtered by `operation`
* transition validations support direct transitions
* bilateral transitions are expanded by the resolver
* transitive transitions are controlled by `allow_transitive_transitions`
* `validate_change()` evaluates changed attributes from a `Change`

Open work:

* ensure parser loads `defaults.validation_rules`
* ensure resolver applies default validation rules to all relevant classes/attributes
* ensure attributes that only exist in default validation rules are resolved even if absent from class-specific attributes

***

# Transition Validation

Implemented model pieces:

```python
TransitionValidation
StateTransitionRule
ValidationResolver
```

Resolver expands:

```yaml
bilateral: true
```

into:

```text
A → B
B → A
```

`allow_transitive_transitions` is a model-level setting.

Default behavior is currently transitive transitions allowed, because XTF imports may move through intermediate states before delivery.

Non-transitive mode is retained for future middleware use cases.

***

# Diff Snapshot Framework

## SnapshotMetadata

Stores:

```python
created_at
source_model
source_class_id
source_object_id
```

## SnapshotObject

Stores:

```python
identity
last_modification
```

where `identity` is:

```python
CanonicalObjectIdentity
```

## SnapshotState

Snapshot lifecycle states:

```python
CURRENT
MODIFIED
DELETED
```

## SnapshotValidationFinding

Stores:

```python
identity
state
```

## DiffSnapshot

Current structure:

```text
DiffSnapshot
├── metadata
├── objects
└── effects
```

Purpose:

```text
Immutable diff review contract
```

***

# DiffSnapshotBuilder

Implemented.

Responsibility:

```text
EffectDocument
        ↓
DiffSnapshot
```

Behavior:

```text
groups effects by canonical object
creates snapshot objects
copies metadata
carries effects forward
```

Unit tests exist.

***

# Snapshot Validation

Implemented:

```python
SnapshotValidationEvaluator
```

Responsibilities:

```text
for each SnapshotObject:
    load current object
    detect deleted object
    compare last_modification
    report modified object
```

Uses:

```python
RelationLookupCapability.current_object()
```

Policy:

```text
last_modification may be optional in the model,
but SnapshotValidationEvaluator raises or reports invalid state when it is
missing where validation requires it.
```

***

# Mapping Framework

Implemented:

```python
ModelMappingCapability
DictionaryMappingCapability
```

Dictionary mapping API follows:

```python
class_mapping_for_ili(...)
attribute_mapping_for_ili(...)
value_mapping_for_ili(...)
```

Open work:

```text
DictionaryMappingCapability.value_mapping_for_ili
DictionaryMappingCapability._load_value_mapping
value mapping tests
```

***

# Adapter Layer

Implemented:

```python
TwwInterlisServiceAdapter
TwwRelationContextProvider
```

Future adapter work:

```text
TwwIntegrityCheckerAdapter
SqlRelationLookupCapability or TWW relation lookup adapter
Persistence adapter
QGIS diff viewer adapter
```

`TwwIntegrityChecker` itself should remain a standalone plugin utility.

***

# Test Architecture

The test suite mirrors the production architecture.

```text
tests/
├── parser/
├── resolver/
├── capabilities/
├── evaluators/
├── services/
├── adapters/
└── interlis/
```

Important test direction:

* use `InMemoryRelationLookupCapability` instead of ad-hoc relation lookup fakes
* keep effect tests aligned with canonical identity JSON
* keep insert validation tests scoped to `operations: [insert]`
* keep recursive derived-right tests explicit

***

# Current Major Contracts

The following contracts are considered important and should not be replaced lightly:

```python
CanonicalObjectIdentity
CanonicalObject

DerivedRights
CanonicalDerivedRights
ResolvedRights

EffectDocument
Effect
UpdateAttributeEffect
EnforceExistsEffect
EnforceNotExistsEffect

Change
ChangeBuilder

DiffSnapshot
SnapshotObject
SnapshotState

ValidationFinding
ValidationContext
ValidationRegistry
ValidationEvaluator

RelationLookupCapability
InMemoryRelationLookupCapability
```

***

# Immediate To-Do

## Rights

* Complete recursive update-right evaluation.
* Ensure derived rights recurse through related objects.
* Ensure subclass rights recurse through the same private update helper.
* Add or finalize tests for:
  * `reach_point -> reach -> wastewater_structure`
  * missing second-hop target rejects update
  * subclass rights recursion
  * cycle protection

## Validation

* Update all direct `validate_attribute()` tests to pass `operation`.
* Remove `operation` from `ValidationContext` unless validators truly need it.
* Parse `defaults.validation_rules`.
* Resolve default validation rules onto class attributes.
* Ensure default validation-only attributes such as `fk_provider` and `fk_dataowner` are resolved even if not explicitly listed under class attributes.
* Add tests for:
  * insert `equals_context_value` mismatch
  * valid insert context values
  * insert-only rules do not apply on update

## Test Data

* Remove accidental global default ownership create rule.
* Replace it with default insert validation rules for:
  * `fk_provider = provider_oid`
  * `fk_dataowner = dataowner_oid`
* Add explicit authorization rules where needed instead of relying on default ownership.

## Relation Lookup

* Keep `RelationLookupCapability` lookup-only.
* Keep `InMemoryRelationLookupCapability` in framework code.
* Add SQL-backed or adapter-backed implementation later.
* Ensure in-memory lookup can support recursive relation chains.

***

# Deferred Work

## Effects

* Define JSON schema.
* Add serialization helpers.
* Add deserialization helpers.
* Add effect persistence interfaces.
* Consider future bulk attribute effect only if single-attribute effects become too verbose.

## Diff Framework

* Build full EffectDocument to Change to DiffSnapshot pipeline.
* Group changes by canonical object.
* Build change summaries.
* Build conflict summaries.
* Support refresh against live database.
* Detect relation graph changes after snapshot creation.

## Snapshot Lifecycle

* Define snapshot refresh strategy.
* Define snapshot invalidation policy.
* Add snapshot revalidation workflow.
* Detect newly inserted related objects.
* Detect deleted related objects.

## Persistence

* Define persistence capability.
* Implement update\_attribute persistence.
* Implement enforce\_exists persistence.
* Implement enforce\_not\_exists persistence.
* Add persistence tests.

## Mapping

* Implement dictionary value mappings.
* Implement AG64 projection functions.
* Implement AG96 projection functions.
* Finalize JSONB effect contract documentation.

## QGIS Diff Viewer

* Define viewer data contract.
* Build object tree representation.
* Build attribute tree representation.
* Build conflict tree representation.
* Add stale snapshot indicators.
* Add severity styling.
* Add conflict styling.
* Add zoom-to-object support.
* Add map highlighting.
* Add filters by:
  * class
  * provider
  * severity
  * data owner

## Adapters

* Add SQL-backed relation lookup or plugin-backed relation lookup.
* Add `TwwIntegrityCheckerAdapter`.
* Finalize non-QGIS adapter test separation.
* Add persistence adapter tests.

## Documentation

* Auto-generate API documentation from metadata.
* Document canonical object model.
* Document relation lookup architecture.
* Document effect JSON contract.
* Document validation rule contract.
* Document derived-right runtime architecture.
* Document snapshot lifecycle.
* Document AGXX projection function contract.

```
```
