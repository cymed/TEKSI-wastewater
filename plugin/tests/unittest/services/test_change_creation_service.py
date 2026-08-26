from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import pytest

from teksi_hooks.models.canonical_object import (
    CanonicalClassMetadata,
    CanonicalModelMetadata,
    CanonicalObjectIdentity,
)
from teksi_hooks.models.effects import (
    EffectDocument,
    EnforceExistsEffect,
    EnforceNotExistsEffect,
    UpdateAttributeEffect,
)
from teksi_hooks.models.review import (
    ReviewFeature
)

from teksi_wastewater.hooks.services import (
    tww_change_creation_service as service_module,
)
from teksi_wastewater.hooks.services.tww_change_creation_service import (
    TwwChangeCreationService,
)
from teksi_wastewater.hooks.services.tww_diff_schema_service import (
    DiffJobMode,
    DiffSchemaWriteResult,
)


def _identity(
    object_id: str,
    *,
    class_id: str = "wastewater_structure",
) -> CanonicalObjectIdentity:
    return CanonicalObjectIdentity(
        class_id=class_id,
        attributes={
            "obj_id": object_id,
        },
    )


def _effect(
    effect_type,
    **attributes: Any,
):
    """
    Construct an effect without depending on unrelated constructor fields.

    The service methods tested here only use identity, attribute_id and the
    concrete effect type. Using the real classes preserves isinstance checks.
    """

    effect = effect_type.__new__(
        effect_type,
    )

    for name, value in attributes.items():
        object.__setattr__(
            effect,
            name,
            value,
        )

    return effect


def _update_effect(
    *,
    identity: CanonicalObjectIdentity,
    attribute_id: str,
    value: Any,
) -> UpdateAttributeEffect:
    return _effect(
        UpdateAttributeEffect,
        identity=identity,
        attribute_id=attribute_id,
        value=value,
    )


def _constraint_effect(
    effect_type,
    *,
    identity: CanonicalObjectIdentity,
):
    return _effect(
        effect_type,
        identity=identity,
    )


def _document(
    *effects,
    source: Any = None,
    version: int = 1,
) -> EffectDocument:
    return EffectDocument(
        source=source,
        effects=tuple(
            effects,
        ),
        created_at=datetime(
            2026,
            1,
            1,
            12,
            0,
            0,
        ),
        version=version,
    )


def _ready_service(
    **overrides,
) -> TwwChangeCreationService:
    values = {
        "effect_projector": Mock(),
        "rights_evaluator_factory": Mock(),
        "object_provider_factory": Mock(),
    }

    values.update(
        overrides,
    )

    return TwwChangeCreationService(
        **values,
    )


def test_change_creation_service_requires_collaborators() -> None:
    service = TwwChangeCreationService(
        effect_projector=None,
        rights_evaluator_factory=None,
        object_provider_factory=None,
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "effect_projector, rights_evaluator_factory, "
            "object_provider_factory"
        ),
    ):
        service._ensure_ready_for_diff_job()


@pytest.mark.parametrize(
    "job_mode",
    (
        DiffJobMode.CREATE,
        DiffJobMode.REPLACE,
    ),
)
def test_change_creation_service_accepts_supported_job_modes(
    job_mode: DiffJobMode,
) -> None:
    service = _ready_service()

    service._assert_supported_job_mode(
        job_mode,
    )


def test_change_creation_service_rejects_refresh_mode() -> None:
    service = _ready_service()

    with pytest.raises(
        NotImplementedError,
        match="refresh is not implemented",
    ):
        service._assert_supported_job_mode(
            DiffJobMode.REFRESH,
        )


def test_change_creation_service_builds_default_import_context() -> None:
    service = _ready_service()

    orgs_path = Path(
        "/tmp/organisations.xtf",
    )

    context = service._import_context(
        context=None,
        schema="xtf_import",
        orgs_path=orgs_path,
    )

    assert context.schema == "xtf_import"
    assert context.import_orgs is True
    assert context.orgs_path == orgs_path


def test_change_creation_service_builds_context_without_organisations() -> None:
    service = _ready_service()

    context = service._import_context(
        context=None,
        schema="xtf_agxx",
        orgs_path=None,
    )

    assert context.schema == "xtf_agxx"
    assert context.import_orgs is False
    assert context.orgs_path is None


def test_change_creation_service_replaces_import_context_values() -> None:
    service = _ready_service()

    original = service._import_context(
        context=None,
        schema="original_schema",
        orgs_path=Path(
            "/tmp/original-organisations.xtf",
        ),
    )

    updated = service._import_context(
        context=original,
        schema="incremental_schema",
        orgs_path=None,
    )

    assert updated is not original
    assert updated.schema == "incremental_schema"
    assert updated.import_orgs is False
    assert updated.orgs_path is None

    assert original.schema == "original_schema"
    assert original.import_orgs is True


def test_change_creation_service_uses_explicit_validation_log_path() -> None:
    service = _ready_service()

    explicit_path = Path(
        "/tmp/explicit.log",
    )

    assert service._validation_log_path(
        validation_log_path=explicit_path,
        xtf_file=Path(
            "/tmp/delivery.xtf",
        ),
        name="validate_import_quarantine",
    ) == explicit_path


def test_change_creation_service_derives_validation_log_path() -> None:
    service = _ready_service()

    assert service._validation_log_path(
        validation_log_path=None,
        xtf_file=Path(
            "/tmp/delivery.xtf",
        ),
        name="validate_import_quarantine",
    ) == Path(
        "/tmp/delivery_validate_import_quarantine.log",
    )


def test_change_creation_service_incremental_updates_override_base_updates() -> None:
    service = _ready_service()

    identity = _identity(
        "ch000000ws000001",
    )

    base_status = _update_effect(
        identity=identity,
        attribute_id="status",
        value="operational",
    )

    base_identifier = _update_effect(
        identity=identity,
        attribute_id="identifier",
        value="Base identifier",
    )

    incremental_status = _update_effect(
        identity=identity,
        attribute_id="status",
        value="inoperative",
    )

    incremental_remark = _update_effect(
        identity=identity,
        attribute_id="remark",
        value="Incremental remark",
    )

    merged = service._merge_effect_documents(
        base_document=_document(
            base_status,
            base_identifier,
            version=1,
        ),
        incremental_document=_document(
            incremental_status,
            incremental_remark,
            version=2,
        ),
    )

    assert merged.effects == (
        incremental_status,
        base_identifier,
        incremental_remark,
    )

    assert merged.version == 2


def test_change_creation_service_keeps_updates_for_different_objects() -> None:
    service = _ready_service()

    first_identity = _identity(
        "ch000000ws000001",
    )

    second_identity = _identity(
        "ch000000ws000002",
    )

    first_status = _update_effect(
        identity=first_identity,
        attribute_id="status",
        value="operational",
    )

    second_status = _update_effect(
        identity=second_identity,
        attribute_id="status",
        value="inoperative",
    )

    merged = service._merge_effect_documents(
        base_document=_document(
            first_status,
        ),
        incremental_document=_document(
            second_status,
        ),
    )

    assert merged.effects == (
        first_status,
        second_status,
    )


def test_change_creation_service_merges_constraint_effects_by_type() -> None:
    service = _ready_service()

    identity = _identity(
        "ch000000ws000001",
    )

    base_exists = _constraint_effect(
        EnforceExistsEffect,
        identity=identity,
    )

    incremental_exists = _constraint_effect(
        EnforceExistsEffect,
        identity=identity,
    )

    incremental_not_exists = _constraint_effect(
        EnforceNotExistsEffect,
        identity=identity,
    )

    merged = service._merge_effect_documents(
        base_document=_document(
            base_exists,
        ),
        incremental_document=_document(
            incremental_exists,
            incremental_not_exists,
        ),
    )

    assert merged.effects == (
        incremental_exists,
        incremental_not_exists,
    )


def test_change_creation_service_rejects_unsupported_effect_type() -> None:
    service = _ready_service()

    unsupported_effect = SimpleNamespace(
        identity=_identity(
            "ch000000ws000001",
        ),
    )

    with pytest.raises(
        TypeError,
        match="Unsupported effect type",
    ):
        service._merge_effect_documents(
            base_document=_document(
                unsupported_effect,
            ),
            incremental_document=_document(),
        )


def test_change_creation_service_builds_one_change_per_identity() -> None:
    identity = _identity(
        "ch000000ws000001",
    )

    status_effect = _update_effect(
        identity=identity,
        attribute_id="status",
        value="operational",
    )

    identifier_effect = _update_effect(
        identity=identity,
        attribute_id="identifier",
        value="Updated identifier",
    )

    constraint_effect = _constraint_effect(
        EnforceExistsEffect,
        identity=identity,
    )

    current_object = object()
    built_change = object()

    relation_lookup = Mock()
    relation_lookup.current_object.return_value = current_object

    change_builder = Mock()
    change_builder.build.return_value = built_change

    service = _ready_service(
        change_builder=change_builder,
    )

    changes = service._build_changes(
        effect_document=_document(
            status_effect,
            identifier_effect,
            constraint_effect,
        ),
        relation_lookup=relation_lookup,
    )

    assert changes == (
        built_change,
    )

    relation_lookup.current_object.assert_called_once_with(
        identity,
    )

    change_builder.build.assert_called_once_with(
        current_object=current_object,
        effects=(
            status_effect,
            identifier_effect,
        ),
    )


def test_change_creation_service_builds_separate_changes_per_identity() -> None:
    first_identity = _identity(
        "ch000000ws000001",
    )

    second_identity = _identity(
        "ch000000ws000002",
    )

    first_effect = _update_effect(
        identity=first_identity,
        attribute_id="status",
        value="operational",
    )

    second_effect = _update_effect(
        identity=second_identity,
        attribute_id="status",
        value="inoperative",
    )

    first_current_object = object()
    second_current_object = object()

    first_change = object()
    second_change = object()

    relation_lookup = Mock()

    relation_lookup.current_object.side_effect = (
        first_current_object,
        second_current_object,
    )

    change_builder = Mock()

    change_builder.build.side_effect = (
        first_change,
        second_change,
    )

    service = _ready_service(
        change_builder=change_builder,
    )

    changes = service._build_changes(
        effect_document=_document(
            first_effect,
            second_effect,
        ),
        relation_lookup=relation_lookup,
    )

    assert changes == (
        first_change,
        second_change,
    )


def test_change_creation_service_ignores_constraint_only_documents() -> None:
    identity = _identity(
        "ch000000ws000001",
    )

    relation_lookup = Mock()
    change_builder = Mock()

    service = _ready_service(
        change_builder=change_builder,
    )

    changes = service._build_changes(
        effect_document=_document(
            _constraint_effect(
                EnforceExistsEffect,
                identity=identity,
            ),
            _constraint_effect(
                EnforceNotExistsEffect,
                identity=identity,
            ),
        ),
        relation_lookup=relation_lookup,
    )

    assert changes == ()

    relation_lookup.current_object.assert_not_called()
    change_builder.build.assert_not_called()


def test_change_creation_service_uses_configured_live_relation_lookup() -> None:
    relation_lookup = Mock()

    service = _ready_service(
        live_relation_lookup=relation_lookup,
    )

    assert service._live_relation_lookup(
        "custom_live_schema",
    ) is relation_lookup


def test_change_creation_service_builds_default_live_relation_lookup(
    monkeypatch,
) -> None:
    relation_lookup = object()
    constructor = Mock(
        return_value=relation_lookup,
    )

    monkeypatch.setattr(
        service_module,
        "TwwRelationLookupAdapter",
        constructor,
    )

    service = _ready_service(
        live_relation_lookup=None,
    )

    result = service._live_relation_lookup(
        "custom_live_schema",
    )

    assert result is relation_lookup

    constructor.assert_called_once_with(
        schema="custom_live_schema",
    )


def test_change_creation_service_requires_incremental_schema() -> None:
    service = _ready_service()

    rights_context = SimpleNamespace(
        provider_oid="ch000000pr000001",
        dataowner_oid="ch000000do000001",
    )

    with pytest.raises(
        ValueError,
        match="incremental_import_schema is required",
    ):
        service.create_diff_job_from_quarantine(
            job_id="job-1",
            job_mode=DiffJobMode.CREATE,
            source_model="DSS_2020_1_LV95",
            rights_context=rights_context,
            incremental_source_model=(
                "Genereller_Entwaesserungsplan_AG"
            ),
            incremental_import_schema=None,
        )


def test_change_creation_service_creates_diff_job_from_quarantine(
    monkeypatch,
) -> None:
    identity = _identity(
        "ch000000ws000001",
    )

    base_status_effect = _update_effect(
        identity=identity,
        attribute_id="status",
        value="operational",
    )

    incremental_status_effect = _update_effect(
        identity=identity,
        attribute_id="status",
        value="inoperative",
    )

    incremental_remark_effect = _update_effect(
        identity=identity,
        attribute_id="remark",
        value="Incremental remark",
    )

    base_document = _document(
        base_status_effect,
        version=1,
    )

    incremental_document = _document(
        incremental_status_effect,
        incremental_remark_effect,
        version=2,
    )

    canonical_metadata = CanonicalModelMetadata(
        classes={
            "wastewater_structure": CanonicalClassMetadata(
                source_id=1,
                identifier="wastewater_structure",
            ),
        },
    )

    canonical_model = Mock()
    canonical_model.canonical_model.return_value = canonical_metadata

    effect_projector = Mock()
    effect_projector.effect_document_from_quarantine.side_effect = (
        base_document,
        incremental_document,
    )

    current_object = object()
    relation_lookup = Mock()
    relation_lookup.current_object.return_value = current_object

    built_change = object()
    change_builder = Mock()
    change_builder.build.return_value = built_change

    rights_evaluator = object()
    rights_evaluator_factory = Mock()
    rights_evaluator_factory.rights_evaluator.return_value = (
        rights_evaluator
    )

    classified_changes = object()
    classifier = Mock()
    classifier.classify.return_value = classified_changes

    classifier_constructor = Mock(
        return_value=classifier,
    )

    monkeypatch.setattr(
        service_module,
        "ChangeClassifier",
        classifier_constructor,
    )

    object_provider = object()
    object_provider_factory = Mock()
    object_provider_factory.change_object_provider.return_value = (
        object_provider
    )

    review_feature = ReviewFeature(
        class_id="wastewater_structure",
        object_id="ch000000ws000001",
        attributes={
            "is_altered": True,
        },
    )

    features_by_class = {
        "wastewater_structure": [
            review_feature,
        ],
    }

    review_service = Mock()
    review_service.export.return_value = features_by_class

    review_service_constructor = Mock(
        return_value=review_service,
    )

    monkeypatch.setattr(
        service_module,
        "ChangeReviewExportService",
        review_service_constructor,
    )

    diff_schema_result = DiffSchemaWriteResult(
        job_db_id=42,
        job_id="job-1",
        row_count=1,
    )

    diff_schema_service = Mock()
    diff_schema_service.write.return_value = diff_schema_result

    rights_context = SimpleNamespace(
        provider_oid="ch000000pr000001",
        dataowner_oid="ch000000do000001",
    )

    service = TwwChangeCreationService(
        canonical_model=canonical_model,
        effect_projector=effect_projector,
        change_builder=change_builder,
        diff_schema_service=diff_schema_service,
        rights_evaluator_factory=rights_evaluator_factory,
        object_provider_factory=object_provider_factory,
        live_relation_lookup=relation_lookup,
    )

    result = service.create_diff_job_from_quarantine(
        job_id="job-1",
        job_mode=DiffJobMode.REPLACE,
        source_model="DSS_2020_1_LV95",
        created_models=(
            "DSS_2020_1_LV95",
        ),
        rights_context=rights_context,
        import_schema="xtf_import",
        live_schema="tww_od",
        incremental_source_model=(
            "Genereller_Entwaesserungsplan_AG"
        ),
        incremental_created_models=(
            "Genereller_Entwaesserungsplan_AG",
        ),
        incremental_import_schema="xtf_agxx",
        metadata={
            "correlation_id": "test-run-1",
        },
    )

    assert result.job_id == "job-1"
    assert result.import_model == "DSS_2020_1_LV95"

    assert (
        result.incremental_import_model
        == "Genereller_Entwaesserungsplan_AG"
    )

    assert result.created_models == [
        "DSS_2020_1_LV95",
    ]

    assert result.incremental_created_models == [
        "Genereller_Entwaesserungsplan_AG",
    ]

    assert result.effect_document is not None

    assert result.effect_document.effects == (
        incremental_status_effect,
        incremental_remark_effect,
    )

    assert result.changes == [
        built_change,
    ]

    assert result.classified_changes is classified_changes
    assert result.features_by_class == features_by_class
    assert result.diff_schema_result is diff_schema_result

    effect_projector.effect_document_from_quarantine.assert_any_call(
        schema="xtf_import",
        source_model="DSS_2020_1_LV95",
        canonical_metadata=canonical_metadata,
    )

    effect_projector.effect_document_from_quarantine.assert_any_call(
        schema="xtf_agxx",
        source_model="Genereller_Entwaesserungsplan_AG",
        canonical_metadata=canonical_metadata,
    )

    change_builder.build.assert_called_once_with(
        current_object=current_object,
        effects=(
            incremental_status_effect,
            incremental_remark_effect,
        ),
    )

    rights_evaluator_factory.rights_evaluator.assert_called_once_with(
        relation_lookup=relation_lookup,
    )

    classifier_constructor.assert_called_once_with(
        rights_evaluator=rights_evaluator,
    )

    classify_call = classifier.classify.call_args

    assert classify_call.kwargs["changes"] == (
        built_change,
    )

    assert classify_call.kwargs["context"] is rights_context

    workflow_metadata = classify_call.kwargs[
        "metadata"
    ]

    assert workflow_metadata == {
        "correlation_id": "test-run-1",
        "job_id": "job-1",
        "job_mode": "replace",
        "source_model": "DSS_2020_1_LV95",
        "import_schema": "xtf_import",
        "live_schema": "tww_od",
        "provider_oid": "ch000000pr000001",
        "dataowner_oid": "ch000000do000001",
        "incremental_source_model": (
            "Genereller_Entwaesserungsplan_AG"
        ),
        "incremental_import_schema": "xtf_agxx",
    }

    object_provider_factory.change_object_provider.assert_called_once_with(
        live_schema="tww_od",
        import_schema="xtf_import",
        canonical_metadata=canonical_metadata,
    )

    review_service.export.assert_called_once_with(
        classified_changes,
    )

    diff_schema_service.write.assert_called_once_with(
        job_id="job-1",
        job_mode=DiffJobMode.REPLACE,
        features_by_class=features_by_class,
        metadata=workflow_metadata,
        validation_success=True,
        job_status="pending",
    )

def test_change_creation_service_imports_base_and_incremental_xtf(
    monkeypatch,
) -> None:
    quarantine_runner = Mock()

    quarantine_runner.import_xtf_to_quarantine.side_effect = (
        (
            "DSS_2020_1_LV95",
            (
                "DSS_2020_1_LV95",
            ),
        ),
        (
            "Genereller_Entwaesserungsplan_AG",
            (
                "Genereller_Entwaesserungsplan_AG",
            ),
        ),
    )

    service = _ready_service(
        quarantine_runner=quarantine_runner,
    )

    delegated_result = object()

    create_from_quarantine = Mock(
        return_value=delegated_result,
    )

    monkeypatch.setattr(
        service,
        "create_diff_job_from_quarantine",
        create_from_quarantine,
    )

    rights_context = SimpleNamespace(
        provider_oid="ch080qwzPR000017",
        dataowner_oid="ch080qwzPR000018",
    )

    xtf_file = Path(
        "/tmp/base.xtf",
    )

    orgs_path = Path(
        "/tmp/organisations.xtf",
    )

    incremental_xtf = Path(
        "/tmp/incremental.xtf",
    )

    result = service.create_diff_job_from_xtf(
        job_id="job-1",
        job_mode=DiffJobMode.CREATE,
        xtf_file=xtf_file,
        rights_context=rights_context,
        orgs_path=orgs_path,
        incremental_xtf=incremental_xtf,
        incremental_import_schema=None,
        import_schema="xtf_import",
        live_schema="tww_od",
        metadata={
            "correlation_id": "run-1",
        },
    )

    assert result is delegated_result

    assert quarantine_runner.import_xtf_to_quarantine.call_count == 2

    base_import_call = (
        quarantine_runner.import_xtf_to_quarantine.call_args_list[0]
    )

    assert base_import_call.kwargs["xtf_file"] == xtf_file
    assert base_import_call.kwargs["schema"] == "xtf_import"
    assert base_import_call.kwargs["context"].schema == "xtf_import"
    assert base_import_call.kwargs["context"].import_orgs is True
    assert base_import_call.kwargs["context"].orgs_path == orgs_path

    incremental_import_call = (
        quarantine_runner.import_xtf_to_quarantine.call_args_list[1]
    )

    assert (
        incremental_import_call.kwargs["xtf_file"]
        == incremental_xtf
    )

    assert incremental_import_call.kwargs[
        "schema"
    ] == "xtf_import_incremental"

    assert (
        incremental_import_call.kwargs["context"].schema
        == "xtf_import_incremental"
    )

    assert (
        incremental_import_call.kwargs["context"].import_orgs
        is False
    )

    assert incremental_import_call.kwargs["context"].orgs_path is None

    assert (
        quarantine_runner.validate_quarantine_or_raise.call_count
        == 2
    )

    base_validation_call = (
        quarantine_runner.validate_quarantine_or_raise.call_args_list[0]
    )

    assert base_validation_call.kwargs["model_names"] == (
        "DSS_2020_1_LV95",
    )

    assert base_validation_call.kwargs["schema"] == "xtf_import"

    assert base_validation_call.kwargs["log_path"] == Path(
        "/tmp/base_validate_import_quarantine.log",
    )

    incremental_validation_call = (
        quarantine_runner.validate_quarantine_or_raise.call_args_list[1]
    )

    assert incremental_validation_call.kwargs["model_names"] == (
        "Genereller_Entwaesserungsplan_AG",
    )

    assert incremental_validation_call.kwargs[
        "schema"
    ] == "xtf_import_incremental"

    assert incremental_validation_call.kwargs["log_path"] == Path(
        "/tmp/incremental_validate_incremental_quarantine.log",
    )

    delegated_call = create_from_quarantine.call_args

    assert delegated_call.kwargs[
        "source_model"
    ] == "DSS_2020_1_LV95"

    assert delegated_call.kwargs[
        "incremental_source_model"
    ] == "Genereller_Entwaesserungsplan_AG"

    assert delegated_call.kwargs[
        "incremental_import_schema"
    ] == "xtf_import_incremental"

    metadata = delegated_call.kwargs[
        "metadata"
    ]

    assert metadata == {
        "correlation_id": "run-1",
        "job_id": "job-1",
        "job_mode": "create",
        "source_model": "DSS_2020_1_LV95",
        "source_file": "/tmp/base.xtf",
        "import_schema": "xtf_import",
        "live_schema": "tww_od",
        "provider_oid": "ch080qwzPR000017",
        "dataowner_oid": "ch080qwzPR000018",
        "orgs_path": "/tmp/organisations.xtf",
        "incremental_xtf": "/tmp/incremental.xtf",
        "incremental_import_schema": "xtf_import_incremental",
        "incremental_source_model": (
            "Genereller_Entwaesserungsplan_AG"
        ),
    }