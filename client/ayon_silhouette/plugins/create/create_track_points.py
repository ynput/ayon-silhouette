import fx

from ayon_core.lib import EnumDef
from ayon_silhouette.api import lib
from ayon_silhouette.api.plugin import SilhouetteCreator


class CreateTrackPoints(SilhouetteCreator):
    """Track Points"""

    identifier = "io.ayon.creators.silhouette.trackpoints"
    label = "Track Points"
    description = __doc__
    product_base_type = "trackpoints"
    product_type = product_base_type
    icon = "cubes"

    create_node_type = "TrackerNode"
    valid_node_types = {"TrackerNode", "RotoNode"}

    def get_attr_defs_for_instance(self, instance):
        node = instance.transient_data["instance_node"]
        items = [
            {"label": label, "value": tracker.id}
            for tracker, label in lib.iter_children(node)
            if isinstance(tracker, fx.Tracker)
        ]
        if not items:
            items.append({
                "label": "<No trackers found>",
                "value": None
            })

        attr_defs = [
            EnumDef(
                "trackers",
                label="Export trackers",
                items=items,
                tooltip="Select trackers to include in output. If none are"
                        " selected then all trackers will be included.",
                multiselection=True,
            )
        ]

        return attr_defs

