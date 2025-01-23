import os

from ayon_core.pipeline import publish
from ayon_silhouette.api import lib

import fx


class SilhouetteExtractAfterEffectsTrack(publish.Extractor):
    """Extract After Effects .txt track from Sillhouette."""
    label = "Extract After Effects .txt"
    hosts = ["silhouette"]
    families = ["trackpoints"]

    extension = "txt"
    io_module = "After Effects"

    def process(self, instance):

        # Define extract output file path
        dir_path = self.staging_dir(instance)
        filename = "{0}.{1}".format(instance.name, self.extension)
        path = os.path.join(dir_path, filename)

        # Node should be a node that contains 'tracker' children
        node = instance.data["transientData"]["instance_node"]
        shapes = node.children

        with lib.maintained_selection():
            fx.select(shapes)
            self.log.debug(f"Exporting '{self.io_module}' to: {path}")
            fx.io_modules[self.io_module].export(path)

        representation = {
            "name": self.extension,
            "ext": self.extension,
            "files": filename,
            "stagingDir": dir_path,
        }
        instance.data.setdefault("representations", []).append(representation)

        self.log.debug(f"Extracted instance '{instance.name}' to: {path}")
