from ayon_server.settings import BaseSettingsModel, SettingsField
from .imageio import ImageIOSettings, DEFAULT_IMAGEIO_SETTINGS
from .templated_workfile_build import (
    TemplatedWorkfileBuildModel
)
from .publish import PublishPluginsModel, DEFAULT_SILHOUETTE_PUBLISH_SETTINGS

class SilhouetteSettings(BaseSettingsModel):
    imageio: ImageIOSettings = SettingsField(
        default_factory=ImageIOSettings,
        title="Color Management (ImageIO)"
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
    "imageio": DEFAULT_IMAGEIO_SETTINGS,
    "publish": DEFAULT_SILHOUETTE_PUBLISH_SETTINGS,
    "templated_workfile_build": {
        "profiles": []
    }
}
