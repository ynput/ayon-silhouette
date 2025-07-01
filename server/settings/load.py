from ayon_server.settings import BaseSettingsModel, SettingsField


class SourceLoaderModel(BaseSettingsModel):
    set_start_frame_on_load: bool = SettingsField(
        default=False,
        title="Set Start Frame on Load",
        description=(
            "When loading a source, set the active session's start frame to "
            "the start frame of the loaded source. This may be helpful "
            "because Silhouette aligns loaded sources with the start frame of "
            "the session."
        ),
    )

class LoadPluginsModel(BaseSettingsModel):
    # Shapes
    SourceLoader: SourceLoaderModel = SettingsField(
        default_factory=SourceLoaderModel,
        title="Load Source",
    )


DEFAULT_SILHOUETTE_LOAD_SETTINGS = {
    "SourceLoader": {
        "set_start_frame_on_load": False,
    }
}
