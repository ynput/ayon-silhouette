import os

from ayon_core.pipeline import (
    publish,
    registered_host
)
from ayon_silhouette.api import lib


class SilhouetteExtractWorkfile(publish.Extractor):
    label = "Extract Workfile"
    hosts = ["silhouette"]
    families = ["workfile"]

    add_project_sfx = False

    def process(self, instance):
        """Extract the current working file as .zip"""
        # Note that Silhouette project workfiles are actually folders,
        # not files.

        current_file = instance.context.data["currentFile"]
        if not current_file:
            raise publish.PublishError("No current file found in context")

        # Save current file
        host = registered_host()
        host.save_workfile()

        # Zip current workfile (Silhouette workfiles are folders)
        staging_dir = self.staging_dir(instance)
        filename = f"{instance.name}.zip"
        lib.zip_folder(current_file, os.path.join(staging_dir, filename))

        # Add representation
        instance.data.setdefault("representations", []).append({
            "name": "sfx_zip",
            "ext": "zip",
            "files": filename,
            "stagingDir": staging_dir,
        })

        if self.add_project_sfx:
            # Add the project.sfx file as a separate representation
            project_sfx = os.path.join(current_file, "project.sfx")

            instance.data.setdefault("representations", []).append({
                "outputName": "project",
                "name": "sfx_project",
                "ext": "sfx",
                "files": os.path.basename(project_sfx),
                "stagingDir": os.path.dirname(project_sfx),
            })
