from ayon_server.settings import BaseSettingsModel, SettingsField
from .session import SessionSettingsModel, DEFAULT_SILHOUETTE_SESSION_SETTINGS
from .imageio import ImageIOSettings, DEFAULT_IMAGEIO_SETTINGS
from .templated_workfile_build import (
    TemplatedWorkfileBuildModel
)
from .publish import PublishPluginsModel, DEFAULT_SILHOUETTE_PUBLISH_SETTINGS
from .load import LoadPluginsModel, DEFAULT_SILHOUETTE_LOAD_SETTINGS

class SilhouetteSettings(BaseSettingsModel):
    session: SessionSettingsModel = SettingsField(
        default_factory=SessionSettingsModel,
        title="Session Default Settings",
    )
    imageio: ImageIOSettings = SettingsField(
        default_factory=ImageIOSettings,
        title="Color Management (ImageIO)"
    )
    load: LoadPluginsModel = SettingsField(
        title="Load",
        default_factory=LoadPluginsModel
    )
    publish: PublishPluginsModel = SettingsField(
        title="Publish",
        default_factory=PublishPluginsModel
    )
    templated_workfile_build: TemplatedWorkfileBuildModel = SettingsField(
        title="Templated Workfile Build",
        default_factory=TemplatedWorkfileBuildModel
    )


DEFAULT_VALUES = {
    "session": DEFAULT_SILHOUETTE_SESSION_SETTINGS,
    "imageio": DEFAULT_IMAGEIO_SETTINGS,
    "load": DEFAULT_SILHOUETTE_LOAD_SETTINGS,
    "publish": DEFAULT_SILHOUETTE_PUBLISH_SETTINGS,
    "templated_workfile_build": {
        "profiles": []
    }
}
