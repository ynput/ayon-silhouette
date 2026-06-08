from ayon_server.settings import BaseSettingsModel, SettingsField


class MenuShortcuts(BaseSettingsModel):
    """Silhouette AYON tool shortcuts."""
    create: str = SettingsField("", title="Create...")
    publish: str = SettingsField("", title="Publish...")
    load: str = SettingsField("", title="Load...")
    manage: str = SettingsField("", title="Manage...")
    workfiles: str = SettingsField("", title="Workfiles...")
    build_workfile: str = SettingsField("", title="Build Workfile...")
    version_up_workfile: str = SettingsField("", title="Version Up Workfile")


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
    shortcuts: MenuShortcuts = SettingsField(
        default_factory=MenuShortcuts,
        title="Shortcuts",
    )


DEFAULT_SILHOUETTE_AYON_MENU_SETTINGS = {
    "set_frame_range": True,
    "set_resolution": True,
    "shortcuts": {
        "create": "ctrl+alt+c",
        "publish": "ctrl+alt+p",
        "load": "ctrl+alt+l",
        "manage": "ctrl+alt+m",
        "build_workfile": "ctrl+alt+b",
        "workfiles": "",
        "version_up_workfile": "alt+shift+s",
    }
}
