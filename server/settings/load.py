from ayon_server.settings import BaseSettingsModel, SettingsField


class SourceLoaderModel(BaseSettingsModel):
    set_session_frame_range_on_load: bool = SettingsField(
        default=False,
        title="Set Session Frame Range on Load",
        description=(
            "When loading a source, set the active session's start frame and "
            "duration to the frame range of the loaded source. This may be "
            "helpful because Silhouette aligns loaded sources with the start "
            "frame of the session."
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
        "set_session_frame_range_on_load": False,
    }
}
