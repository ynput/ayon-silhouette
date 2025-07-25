import os

import pyblish.api

from ayon_core.lib import version_up
from ayon_core.host import IWorkfileHost
from ayon_core.pipeline import registered_host
from ayon_core.pipeline.publish import (
    KnownPublishError,
    OptionalPyblishPluginMixin
)


class IncrementCurrentFile(pyblish.api.ContextPlugin,
                           OptionalPyblishPluginMixin):
    """Increment the current file.

    Saves the current scene with an increased version number.
    """
    label = "Increment current file"
    order = pyblish.api.IntegratorOrder + 9.0
    families = ["*"]
    hosts = ["silhouette"]
    optional = True

    def process(self, context):
        if not self.is_active(context.data):
            return

        # Filename must not have changed since collecting.
        host = registered_host()
        current_filepath: str = host.get_current_workfile()
        if context.data["currentFile"] != current_filepath:
            raise KnownPublishError(
                f"Collected filename '{context.data['currentFile']}' differs"
                f" from current scene name '{current_filepath}'."
            )

        try:
            from ayon_core.pipeline.workfile import save_next_version
            from ayon_core.host.interfaces import SaveWorkfileOptionalData

            current_filename = os.path.basename(current_filepath)
            save_next_version(
                description=(
                    f"Incremented by publishing from {current_filename}"
                ),
                # Optimize the save by reducing needed queries for context
                prepared_data=SaveWorkfileOptionalData(
                    project_entity=context.data["projectEntity"],
                    project_settings=context.data["project_settings"],
                    anatomy=context.data["anatomy"],
                )
            )
        except ImportError:
            # Backwards compatibility before ayon-core 1.5.0
            self.log.debug(
                "Using legacy `version_up`. Update AYON core addon to "
                "use newer `save_next_version` function."
            )
            new_filepath = version_up(current_filepath)
            host: IWorkfileHost = registered_host()
            host.save_workfile(new_filepath)
