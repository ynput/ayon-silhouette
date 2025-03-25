import os
import contextlib
from typing import Optional

from qtpy import QtWidgets
import fx

from ayon_core.pipeline import publish
from ayon_silhouette.api import lib


class ExtractNukeShapes(publish.Extractor,
                        publish.OptionalPyblishPluginMixin):
    """Extract node as Nuke 9+ Shapes."""

    label = "Extract Nuke 9+ Shapes"
    hosts = ["silhouette"]
    families = ["matteshapes"]

    extension = "nk"
    io_module = "Nuke 9+ Shapes"

    # When set, override the representation name and `outputName`
    override_name: Optional[str] = None

    settings_category = "silhouette"

    capture_messageboxes = False

    def process(self, instance):
        if not self.is_active(instance.data):
            return

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
                shape for shape, _label in lib.iter_children(node)
                if isinstance(shape, fx.Shape)
            ]

        with lib.maintained_selection():
            fx.select(shapes)
            with contextlib.ExitStack() as stack:
                self.log.debug(f"Exporting '{self.io_module}' to: {path}")
                if self.capture_messageboxes:
                    stack.enter_context(
                        lib.capture_messageboxes(self.on_captured_messagebox))
                fx.io_modules[self.io_module].export(path)

        representation = {
            "name": self.override_name or self.extension,
            "ext": self.extension,
            "files": filename,
            "stagingDir": dir_path,
        }
        if self.override_name:
            representation["outputName"] = self.override_name
        instance.data.setdefault("representations", []).append(representation)

        self.log.debug(f"Extracted instance '{instance.name}' to: {path}")

    def on_captured_messagebox(self, messagebox: QtWidgets.QMessageBox):
        pass


class ExtractNuke62Shapes(ExtractNukeShapes):
    """Extract node as Nuke 6.2+ Shapes."""
    families = ["matteshapes"]
    label = "Extract Nuke 6.2+ Shapes"
    io_module = "Nuke 6.2+ Shapes"

    # Use nk62 name to avoid conflicts with the nuke 9+ shapes output
    override_name = "nk62"


class ExtractFusionShapes(ExtractNukeShapes):
    """Extract node as Fusion Shapes."""
    # TODO: Suppress a pop-up dialog
    families = ["matteshapes"]
    label = "Extract Fusion Shapes"
    extension = "setting"
    io_module = "Fusion Shapes"

    capture_messageboxes = True

    def on_captured_messagebox(self, messagebox):
        # Suppress pop-up dialogs
        self.log.debug(f"Detected messagebox: {messagebox.text()}")

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
