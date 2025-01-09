import os

from ayon_core.pipeline import publish
from ayon_silhouette.api import lib

import fx


class ExtractNukeShapes(publish.Extractor):
    """Extract node as Nuke 9+ Shapes."""

    label = "Extract Nuke 9+ Shapes"
    hosts = ["silhouette"]
    families = ["trackpoints", "matteshapes"]

    def process(self, instance):

        # Define extract output file path
        dir_path = self.staging_dir(instance)
        filename = "{0}.nk".format(instance.name)
        path = os.path.join(dir_path, filename)

        node = instance.data["transientData"]["instance_node"]
        shapes = node.children

        with lib.maintained_selection():
            fx.select(shapes)
            fx.io_modules["Nuke 9+ Shapes"].export(path)

        representation = {
            "name": "nk",
            "ext": "nk",
            "files": filename,
            "stagingDir": dir_path,
        }
        instance.data.setdefault("representations", []).append(representation)

        self.log.info(f"Extracted instance '{instance.name}' to: {path}")