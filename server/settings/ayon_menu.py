from ayon_server.settings import BaseSettingsModel, SettingsField


class AyonMenuSettingsModel(BaseSettingsModel):
    """Customize top AYON menu in Silhouette."""
    set_frame_range: bool = SettingsField(
        True,
        title="Set Frame Range",
        description=(
            "Set active Session frame range and FPS to match current task "
            "context."
        ),
    )
    set_resolution: bool = SettingsField(
        True,
        title="Set Resolution",
        description=(
            "Set active Session resolution to match current task context."
        ),
    )


DEFAULT_SILHOUETTE_AYON_MENU_SETTINGS = {
    "set_frame_range": True,
    "set_resolution": True,
}
