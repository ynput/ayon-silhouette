import os
import contextlib

from qtpy import QtCore, QtWidgets
import fx

from ayon_core.pipeline import publish
from ayon_silhouette.api import lib


@contextlib.contextmanager
def capture_messageboxes(callback):
    """Capture messageboxes and call a callback with them.

    This is a workaround for Silhouette not allowing the Python code to
    suppress messageboxes and supply default answers to them. So instead we
    capture the messageboxes and respond to them through a rapid QTimer.
    """
    processed = set()
    timer = QtCore.QTimer()

    def on_timeout():
        # Check for dialogs
        widgets = QtWidgets.QApplication.instance().topLevelWidgets()
        has_boxes = False
        for widget in widgets:
            if isinstance(widget, QtWidgets.QMessageBox):
                has_boxes = True
                if widget in processed:
                    continue
                processed.add(widget)
                callback(widget)
        if not has_boxes:
            # Stop as soon as possible with our detections. Even with the
            # QTimer repeating at interval of 0 we should have been able to
            # capture all the UI events as they happen in the main thread for
            # each dialog.
            timer.stop()

    timer.setSingleShot(False)  # Allow to capture multiple boxes
    timer.timeout.connect(on_timeout)
    timer.start()
    try:
        yield
    finally:
        timer.stop()


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
            with capture_messageboxes(self.on_captured_messagebox):
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
        # Suppress a pop-up dialog
        self.log.debug(f"Detected messagebox: {messagebox.text()}")


class ExtractFusionShapes(ExtractNukeShapes):
    """Extract node as Fusion Shapes."""
    # TODO: Suppress a pop-up dialog
    families = ["matteshapes"]
    label = "Extract Fusion Shapes"
    extension = "setting"
    io_module = "Fusion Shapes"

    def on_captured_messagebox(self, messagebox):
        super().on_captured_messagebox(messagebox)

        def click(messagebox: QtWidgets.QMessageBox, text: str):
            """Click QMessageBox button with matching text."""
            self.log.debug(f"Accepting messagebox with '{text}'")
            button = next(
                button for button in messagebox.buttons()
                if button.text() == text
            )
            button.click()

        messagebox_text = messagebox.text()
        if messagebox_text == "Output Fusion Groups?":
            click(messagebox, "&Yes")
        elif messagebox_text == "Link Shapes?":
            click(messagebox, "&Yes")


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
