import os
from ayon_core.addon import AYONAddon, IHostAddon

from .version import __version__

SILHOUETTE_ADDON_ROOT = os.path.dirname(os.path.abspath(__file__))


class SilhouetteAddon(AYONAddon, IHostAddon):
    name = "silhouette"
    version = __version__
    host_name = "silhouette"

    def add_implementation_envs(self, env, app):
        # Set default values if are not already set via settings
        defaults = {"AYON_LOG_NO_COLORS": "1"}
        for key, value in defaults.items():
            if not env.get(key):
                env[key] = value

        # Add startup scripts
        script_key = "SFX_SCRIPT_IMPORTS"
        paths = env.get(script_key, "").split(os.pathsep)
        paths.append(os.path.join(SILHOUETTE_ADDON_ROOT, "startup"))

        # Ignore empty paths
        paths = [path for path in paths if path]
        env[script_key] = os.pathsep.join(paths)

    def get_workfile_extensions(self):
        return [".sfx"]
