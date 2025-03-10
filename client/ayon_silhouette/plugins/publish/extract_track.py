import contextlib
import os

from qtpy import QtWidgets

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

    settings_category = "silhouette"

    capture_messageboxes = True

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
                tracker for tracker, _label in lib.iter_children(node)
                if isinstance(tracker, fx.Tracker)
            ]

        with lib.maintained_selection():
            fx.select(trackers)
            with contextlib.ExitStack() as stack:
                self.log.debug(f"Exporting '{self.io_module}' to: {path}")
                if self.capture_messageboxes:
                    stack.enter_context(
                        lib.capture_messageboxes(self.on_captured_messagebox))
                fx.io_modules[self.io_module].export(path)

        representation = {
            "name": self.extension,
            "ext": self.extension,
            "files": filename,
            "stagingDir": dir_path,
        }
        instance.data.setdefault("representations", []).append(representation)

        self.log.debug(f"Extracted instance '{instance.name}' to: {path}")

    def on_captured_messagebox(self, messagebox: QtWidgets.QMessageBox):
        self.log.debug(f"Detected messagebox: {messagebox.text()}")
        button_texts = [button.text() for button in messagebox.buttons()]
        self.log.debug(f"Buttons: {button_texts}")
        # Continue if messagebox is just confirmation dialog about After
        # Effects being unable to keyframe Match Size, Search Offset and Search
        # Size.
        if "After Effects cannot keyframe" in messagebox.text():
            self.click(messagebox, "&Yes")

    def click(self, messagebox: QtWidgets.QMessageBox, text: str):
        """Click QMessageBox button with matching text."""
        self.log.debug(f"Accepting messagebox with '{text}'")
        button = next(
            button for button in messagebox.buttons()
            if button.text() == text
        )
        button.click()


class SilhouetteExtractNuke5Track(SilhouetteExtractAfterEffectsTrack):
    """Extract Nuke 5 .nk trackers from Silhouette."""
    label = "Extract Nuke 5 Trackers"
    hosts = ["silhouette"]
    families = ["trackpoints"]

    extension = "nk"
    io_module = "Nuke 5"

    # Whether or not to merge up to four trackers in a single Nuke Tracker node
    # or otherwise export as multiple single point tracker nodes
    merge_up_to_four = True

    def on_captured_messagebox(self, messagebox: QtWidgets.QMessageBox):
        self.log.debug(f"Detected messagebox: {messagebox.text()}")
        button_texts = [button.text() for button in messagebox.buttons()]
        self.log.debug(f"Buttons: {button_texts}")
        # Merge up to four tracker
        if "Select Yes to merge." in messagebox.text():
            button = "&Yes" if self.merge_up_to_four else "&No"
            self.click(messagebox, button)
