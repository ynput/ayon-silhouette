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
        node = instance.transient_data["instance_node"]
        items = [
            {"label": label, "value": shape.id}
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
