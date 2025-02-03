from ayon_silhouette.api import plugin


class ShapesLoader(plugin.SilhouetteImportLoader):

    color = "orange"
    product_types = {"matteshapes"}
    icon = "code-fork"
    label = "Load Shapes"
    order = -5
    representations = {"*"}
    extensions = {"fxs"}

    io_module = "Silhouette Shapes"
    # TODO: Support "Commotion Shapes"
    # TODO: Support "Elastic Reality Shapes"
    # TODO: Support "Shake 4.x SSF"

    def can_import_to_node(self, node) -> bool:
        if not super().can_import_to_node(node):
            return False

        return node.supportsChildType("Shape")
