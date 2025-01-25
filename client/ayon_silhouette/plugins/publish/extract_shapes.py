import os

from ayon_core.pipeline import publish
from ayon_silhouette.api import lib

import fx


class ExtractNukeShapes(publish.Extractor):
    """Extract node as Nuke 9+ Shapes."""

    label = "Extract Nuke 9+ Shapes"
    hosts = ["silhouette"]
    families = ["matteshapes"]

    extension = "nk"
    io_module = "Nuke 9+ Shapes"

    def process(self, instance):

        # Define extract output file path
        dir_path = self.staging_dir(instance)
        filename = "{0}.{1}".format(instance.name, self.extension)
        path = os.path.join(dir_path, filename)

        node = instance.data["transientData"]["instance_node"]

        # Use selection, if any specified, otherwise use all children shapes
        shape_ids = instance.data.get("creator_attributes", {}).get("shapes")
        if shape_ids:
            shapes = [fx.findObject(shape_id) for shape_id in shape_ids]
        else:
            shapes = [
                shape for shape in node.children if isinstance(shape, fx.Shape)
            ]

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


class ExtractFusionShapes(ExtractNukeShapes):
    """Extract node as Fusion Shapes."""
    # TODO: Suppress a pop-up dialog
    families = ["matteshapes"]
    label = "Extract Fusion Shapes"
    extension = "setting"
    io_module = "Fusion Shapes"


class ExtractSilhouetteShapes(ExtractNukeShapes):
    """Extract node as Silhouette Shapes."""
    families = ["matteshapes"]
    label = "Extract Silhouette Shapes"
    extension = "fxs"
    io_module = "Silhouette Shapes"


class ExtractShakeShapes(ExtractNukeShapes):
    """Extract node as Shake Shapes."""
    families = ["matteshapes"]
    label = "Extract Shape Shapes"
    extension = "ssf"
    io_module = "Shake 4.x SSF"
