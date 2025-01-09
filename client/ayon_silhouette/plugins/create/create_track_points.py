from ayon_silhouette.api import plugin


class CreateTrackPoints(plugin.SilhouetteCreator):
    """Track Points"""

    identifier = "io.ayon.creators.silhouette.trackpoints"
    label = "Track Points"
    description = __doc__
    product_type = "trackpoints"
    icon = "cubes"

    node_type = "TrackerNode"
