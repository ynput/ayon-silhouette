import os

import fx

from ayon_core.pipeline import publish
from ayon_silhouette.api import lib


class SilhouetteExtractAfterEffectsTrack(publish.Extractor):
    """Extract After Effects .txt track from Silhouette."""
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


        # Use selection, if any specified, otherwise use all children shapes
        tracker_ids = instance.data.get(
            "creator_attributes", {}).get("trackers")
        if tracker_ids:
            trackers = [
                fx.findObject(tracker_id) for tracker_id in tracker_ids
            ]
        else:
            trackers = [
                tracker for tracker in node.children
                if isinstance(tracker, fx.Tracker)
            ]

        with lib.maintained_selection():
            fx.select(trackers)
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


class SilhouetteExtractNuke5Track(SilhouetteExtractAfterEffectsTrack):
    """Extract Nuke 5 .nk trackers from Silhouette."""
    label = "Extract Nuke 5 Trackers"
    hosts = ["silhouette"]
    families = ["trackpoints"]

    extension = "nk"
    io_module = "Nuke 5"
