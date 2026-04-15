from ayon_server.settings import BaseSettingsModel, SettingsField
from .ayon_menu import (
    AyonMenuSettingsModel,
    DEFAULT_SILHOUETTE_AYON_MENU_SETTINGS
)
from .session import SessionSettingsModel, DEFAULT_SILHOUETTE_SESSION_SETTINGS
from .imageio import ImageIOSettings, DEFAULT_IMAGEIO_SETTINGS
from .templated_workfile_build import (
    TemplatedWorkfileBuildModel
)
from .create import CreatePluginsModel, DEFAULT_SILHOUETTE_CREATE_SETTINGS
from .publish import PublishPluginsModel, DEFAULT_SILHOUETTE_PUBLISH_SETTINGS
from .load import LoadPluginsModel, DEFAULT_SILHOUETTE_LOAD_SETTINGS


class SilhouetteSettings(BaseSettingsModel):
    ayon_menu: AyonMenuSettingsModel = SettingsField(
        default_factory=AyonMenuSettingsModel,
        title="AYON Menu",
    )
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
    create: CreatePluginsModel = SettingsField(
        title="Create",
        default_factory=CreatePluginsModel
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
    "ayon_menu": DEFAULT_SILHOUETTE_AYON_MENU_SETTINGS,
    "session": DEFAULT_SILHOUETTE_SESSION_SETTINGS,
    "imageio": DEFAULT_IMAGEIO_SETTINGS,
    "load": DEFAULT_SILHOUETTE_LOAD_SETTINGS,
    "create": DEFAULT_SILHOUETTE_CREATE_SETTINGS,
    "publish": DEFAULT_SILHOUETTE_PUBLISH_SETTINGS,
    "templated_workfile_build": {
        "profiles": []
    }
}
