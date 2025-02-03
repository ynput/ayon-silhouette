from ayon_silhouette.api import plugin


class TrackPointsLoader(plugin.SilhouetteImportLoader):
    """Load track points."""

    color = "orange"
    product_types = {"trackpoints"}
    icon = "code-fork"
    label = "Load Trackers"
    order = -5
    representations = {"*"}
    extensions = {"txt"}

    io_module = "After Effects Corner-Pin"
    # TODO: Support "Nuke"           # .nk
    # TODO: Support "Nuke 5"         # .nk
    # TODO: Support "Shake"          # .txt
    # TODO: Support "Simple Format"  # .txt

    def can_import_to_node(self, node) -> bool:
        if not super().can_import_to_node(node):
            return False

        return node.supportsChildType("Tracker")
