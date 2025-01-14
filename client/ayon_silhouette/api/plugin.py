from ayon_core.pipeline import (
    Creator,
    LoaderPlugin,
    CreatedInstance,
    AYON_INSTANCE_ID,
    AVALON_INSTANCE_ID,
    CreatorError,
)
from ayon_core.lib import BoolDef
from . import lib

import fx


def cache_instance_data(shared_data):
    """Cache instances for Creators shared data.

    Create `silhouette_cached_instances` key when needed in shared data and
    fill it with all collected instances from the scene under its
    respective creator identifiers.

    Args:
        shared_data(Dict[str, Any]): Shared data.

    """
    if shared_data.get('silhouette_cached_instances') is None:
        shared_data["silhouette_cached_instances"] = cache = {}

        session = fx.activeSession()
        if not session:
            return

        instance_ids = {AYON_INSTANCE_ID, AVALON_INSTANCE_ID}
        for node in session.nodes:
            data = lib.read(node)
            if not data:
                continue

            if data.get("id") not in instance_ids:
                continue

            creator_id = data.get("creator_identifier")
            if not creator_id:
                continue

            cache.setdefault(creator_id, []).append(node)

    return shared_data


class SilhouetteCreator(Creator):
    default_variants = ['Main']
    settings_category = "silhouette"

    node_type = "OutputNode"

    @lib.undo_chunk("Create instance")
    def create(self, product_name, instance_data, pre_create_data):

        session = fx.activeSession()
        if not session:
            return

        instance_node = None
        if pre_create_data.get("use_selection"):
            # Allow to imprint on a currently selected node of the same type
            # as this creator would generate. If the node is already imprinted
            # by a Creator then raise an error - otherwise use it as the
            # instance node.
            selection = fx.selection()
            for node in selection:
                if node.type == self.node_type:
                    data = lib.read(node)
                    if data and data.get("creator_identifier"):
                        raise CreatorError(
                            "Selected node is already imprinted by a Creator."
                        )
                    instance_node = node
                    self.log.debug(
                        f"Using selected node as instance node: {node.label}")
                    break

        if instance_node is None:
            # Create new node and place it in the scene
            instance_node = fx.Node(self.node_type)
            instance_node.label = session.uniqueLabel(product_name)
            session.addNode(instance_node)
            lib.set_new_node_position(instance_node)

        fx.activate(instance_node)

        # Enforce forward compatibility to avoid the instance to default
        # to the legacy `AVALON_INSTANCE_ID`
        instance_data["id"] = AYON_INSTANCE_ID
        # Use the uniqueness of the node in Silhouette as the instance id
        instance_data["instance_id"] = instance_node.id
        instance = CreatedInstance(
            product_type=self.product_type,
            product_name=product_name,
            data=instance_data,
            creator=self,
        )

        # Store the instance data
        data = instance.data_to_store()
        self._imprint(instance_node, data)

        # Insert the transient data
        instance.transient_data["instance_node"] = instance_node

        self._add_instance_to_context(instance)

        return instance

    def collect_instances(self):
        shared_data = cache_instance_data(self.collection_shared_data)
        for obj in shared_data["silhouette_cached_instances"].get(
                self.identifier, []):

            data = lib.read(obj)
            data["instance_id"] = str(obj.id)

            # Add instance
            created_instance = CreatedInstance.from_existing(data, self)

            # Collect transient data
            created_instance.transient_data["instance_node"] = obj

            self._add_instance_to_context(created_instance)

    @lib.undo_chunk("Update instances")
    def update_instances(self, update_list):
        for created_inst, _changes in update_list:
            new_data = created_inst.data_to_store()
            node = created_inst.transient_data["instance_node"]
            self._imprint(node, new_data)

    @lib.undo_chunk("Remove instances")
    def remove_instances(self, instances):
        for instance in instances:

            # Remove node from the scene
            node = instance.transient_data["instance_node"]
            if node:
                session = node.session
                session.removeNode(node)

            # Remove the collected CreatedInstance to remove from UI directly
            self._remove_instance_from_context(instance)

    def _imprint(self, node, data):
        # Do not store instance id since it's the Silhouette node id
        data.pop("instance_id", None)
        lib.imprint(node, data)

    def get_pre_create_attr_defs(self):
        return [
            BoolDef("use_selection",
                    label="Use selection",
                    default=True)
        ]


class SilhouetteLoader(LoaderPlugin):
    settings_category = "silhouette"
    hosts = ["silhouette"]
