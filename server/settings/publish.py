from ayon_server.settings import BaseSettingsModel, SettingsField


class BasicEnabledStatesModel(BaseSettingsModel):
    enabled: bool = SettingsField(
        title="Enabled", description="Whether the plug-in is enabled"
    )
    optional: bool = SettingsField(
        title="Optional",
        description=(
            "If the plug-in is enabled, this defines whether it can be "
            "activated or deactivated by the artist in the publisher UI."
        ),
    )
    active: bool = SettingsField(
        title="Active",
        description=(
            "If the plug-in is optional, this defines the default "
            "enabled state."
        ),
    )


class SilhouetteExtractWorkfileModel(BaseSettingsModel):
    add_project_sfx: bool = SettingsField(
        False,
        title="Add project.sfx representation",
        description=(
            "Add the project.sfx file as a separate `sfx_project` "
            "representation."
        ),
    )


class PublishPluginsModel(BaseSettingsModel):
    # Shapes
    ExtractNukeShapes: BasicEnabledStatesModel = SettingsField(
        default_factory=BasicEnabledStatesModel,
        title="Extract Nuke 9+ .nk Shapes",
        section="Extract Shapes",
    )
    ExtractNuke62Shapes: BasicEnabledStatesModel = SettingsField(
        default_factory=BasicEnabledStatesModel,
        title="Extract Nuke 6.2+ .nk Shapes",
    )
    ExtractSilhouetteShapes: BasicEnabledStatesModel = SettingsField(
        default_factory=BasicEnabledStatesModel,
        title="Extract Silhouette .fxs Shapes.",
    )
    ExtractShakeShapes: BasicEnabledStatesModel = SettingsField(
        default_factory=BasicEnabledStatesModel,
        title="Extract Shake 4.x .ssf Shapes",
    )
    ExtractFusionShapes: BasicEnabledStatesModel = SettingsField(
        default_factory=BasicEnabledStatesModel,
        title="Extract Fusion .settings Shapes",
    )

    # Trackers
    SilhouetteExtractAfterEffectsTrack: BasicEnabledStatesModel = (
        SettingsField(
            default_factory=BasicEnabledStatesModel,
            title="Extract After Effects .txt Trackers",
            section="Extract Trackers",
        )
    )
    SilhouetteExtractNuke5Track: BasicEnabledStatesModel = SettingsField(
        default_factory=BasicEnabledStatesModel,
        title="Extract Nuke 5 .nk Trackers",
    )

    # Workfile
    SilhouetteExtractWorkfile: SilhouetteExtractWorkfileModel = SettingsField(
        default_factory=SilhouetteExtractWorkfileModel,
        title="Extract Workfile",
        section="Extract Workfile",
    )


DEFAULT_SILHOUETTE_PUBLISH_SETTINGS = {
    "ExtractNukeShapes": {
        "enabled": True,
        "optional": False,
        "active": True,
    },
    "ExtractNuke62Shapes": {
        "enabled": False,
        "optional": False,
        "active": True,
    },
    "ExtractSilhouetteShapes": {
        "enabled": True,
        "optional": False,
        "active": True,
    },
    "ExtractShakeShapes": {
        "enabled": False,
        "optional": False,
        "active": True,
    },
    "ExtractFusionShapes": {
        "enabled": False,
        "optional": False,
        "active": True,
    },
    "SilhouetteExtractAfterEffectsTrack": {
        "enabled": True,
        "optional": False,
        "active": True,
    },
    "SilhouetteExtractNuke5Track": {
        "enabled": True,
        "optional": False,
        "active": True,
    },
    "SilhouetteExtractWorkfile": {
        "add_project_sfx": False,
    },
}
