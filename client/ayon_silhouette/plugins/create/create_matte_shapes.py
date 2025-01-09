from ayon_silhouette.api import plugin


class CreateMatteShapes(plugin.SilhouetteCreator):
    """Matte Shapes"""

    identifier = "io.ayon.creators.silhouette.matteshapes"
    label = "Matte Shapes"
    description = __doc__
    product_type = "matteshapes"
    icon = "cubes"

    node_type = "RotoNode"
