import fx

from ayon_core.lib import EnumDef
from ayon_silhouette.api import plugin, lib


class CreateMatteShapes(plugin.SilhouetteCreator):
    """Matte Shapes"""

    identifier = "io.ayon.creators.silhouette.matteshapes"
    label = "Matte Shapes"
    description = __doc__
    product_type = "matteshapes"
    icon = "cubes"

    create_node_type = "RotoNode"

    def get_attr_defs_for_instance(self, instance):
        # Unfortunately in Creator.get_attr_defs_for_instance we can't access
        # any transient data because this gets called on `__init__` of the
        # instance directly, not after transient data was added to the instance
        # in the `create` or `collect` method. So we must find the node by
        # node id.
        node_id = instance.data.get("instance_id")
        node = fx.findObject(node_id)

        if not node:
            return []

        items = [
            {"label": label, "value": shape}
            for shape, label in lib.iter_children(node)
            if isinstance(shape, fx.Shape)
        ]
        if not items:
            items.append({
                "label": "<No shapes found>",
                "value": None
            })

        attr_defs = [
            EnumDef(
                "shapes",
                label="Export shapes",
                items=items,
                tooltip="Select shapes to include in matte shapes output. If "
                        "none are selected then all shapes will be included.",
                multiselection=True,
            )
        ]

        return attr_defs
