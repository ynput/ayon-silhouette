import fx

from ayon_core.lib import EnumDef, UILabelDef
from ayon_silhouette.api import plugin


class CreateTrackPoints(plugin.SilhouetteCreator):
    """Track Points"""

    identifier = "io.ayon.creators.silhouette.trackpoints"
    label = "Track Points"
    description = __doc__
    product_type = "trackpoints"
    icon = "cubes"

    create_node_type = "TrackerNode"
    valid_node_types = {"TrackerNode", "RotoNode"}

    def get_attr_defs_for_instance(self, instance):
        # Unfortunately in Creator.get_attr_defs_for_instance we can't access
        # any transient data because this gets called on `__init__` of the
        # instance directly, not after transient data was added to the instance
        # in the `create` or `collect` method. So we must find the node by
        # node id.
        node_id = instance.data.get("node_id")
        node = fx.findObject(node_id)

        if not node:
            return []

        trackers = [
            tracker for tracker in node.children
            if isinstance(tracker, fx.Tracker)
        ]
        # Iterate reversed so they appear as same order in the object list
        # in Silhouette user interface
        items = []
        for tracker in reversed(trackers):
            items.append({
                "label": tracker.label,
                "value": tracker.id
            })


        if not items:
            items.append({
                "label": "<No trackers found>",
                "value": None
            })

        attr_defs = [
            UILabelDef(f"<b>Node</b>: {node.label}", key="node_label"),
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

