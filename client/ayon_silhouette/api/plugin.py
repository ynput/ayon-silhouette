import uuid
import fx

from ayon_core.pipeline import (
    Creator,
    LoaderPlugin,
    CreatedInstance,
    AYON_INSTANCE_ID,
    CreatorError,
)
from ayon_core.lib import BoolDef
from . import lib

INSTANCES_DATA_KEY = "AYON_instances"


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

        for node in session.nodes:
            instances_data_by_uuid = lib.read(node, key=INSTANCES_DATA_KEY)
            if not instances_data_by_uuid:
                continue

            for instance_uuid, data in instances_data_by_uuid.items():
                if data.get("id") != AYON_INSTANCE_ID:
                    continue

                creator_id = data.get("creator_identifier")
                if not creator_id:
                    continue

                cache.setdefault(creator_id, []).append(
                    (node, instance_uuid, data))

    return shared_data


class SilhouetteCreator(Creator):
    """Base class for Silhouette creators.

    This base creator can be applied multiple times to a single node, where
    each instance is stored as a separate imprint on the node, inside an
    `AYON_instances` state that is a `dict[str, dict]` of instance data per
    uuid. The `instance_id` will then be defined by the node's id and this uuid
    as `{node_id}|{uuid}`.

    This way, a single RotoNode can have multiple instances of different
    product types (or even the same product type) to allow exporting e.g.
    track points and matte shapes from the same RotoNode.

    """
    default_variants = ["Main"]
    settings_category = "silhouette"

    create_node_type = "OutputNode"

    # When `valid_node_types` is set, all these node types are allowed to get
    # imprinted by this creator
    valid_node_types = set()

    @lib.undo_chunk("Create instance")
    def create(self, product_name, instance_data, pre_create_data):

        session = fx.activeSession()
        if not session:
            return

        instance_node = None
        use_selection = pre_create_data.get("use_selection")
        selected_nodes = []
        if use_selection:
            # Allow to imprint on a currently selected node of the same type
            # as this creator would generate. If the node is already imprinted
            # by a Creator then raise an error - otherwise use it as the
            # instance node.
            valid_node_types = self.valid_node_types or {self.create_node_type}
            selected_nodes = [
                node for node in fx.selection() if isinstance(node, fx.Node)]
            for node in selected_nodes:
                if node.type in valid_node_types:
                    data = lib.read(node)
                    if data and data.get("creator_identifier"):
                        raise CreatorError(
                            "Selected node is already imprinted by a Creator."
                        )
                    instance_node = node
                    self.log.info(
                        f"Using selected node as instance node: {node.label}")
                    break

        if instance_node is None:
            # Create new node and place it in the scene
            instance_node = fx.Node(self.create_node_type)
            session.addNode(instance_node)
            lib.set_new_node_position(instance_node)

            # When generating a new instance node and use selection is enabled,
            # connect to the first selected node with a matching output type
            if use_selection and selected_nodes:
                self._connect_input_to_first_matching_candidate(
                    instance_node, selected_nodes)

            instance_node.label = session.uniqueLabel(product_name)
        fx.activate(instance_node)

        # Use the uniqueness of the node in Silhouette as part of the instance
        # id, but because we support multiple instances per node, we also add
        # an uuid within the node to make duplicates of nodes still unique in
        # the full create context.
        instance_id = f"{instance_node.id}|{uuid.uuid4()}"
        instance_data["instance_id"] = instance_id
        instance_data["label"] = self._define_label(
            instance_node, product_name)
        instance = CreatedInstance(
            product_type=self.product_type,
            product_name=product_name,
            data=instance_data,
            creator=self,
            transient_data={
                "instance_node": instance_node
            }
        )

        # Store the instance data
        data = instance.data_to_store()
        self._imprint(instance_node, data)

        self._add_instance_to_context(instance)

        return instance

    def collect_instances(self):
        shared_data = cache_instance_data(self.collection_shared_data)
        cached_instances = shared_data["silhouette_cached_instances"]
        for obj, instance_uuid, data in cached_instances.get(
                self.identifier, []):
            data["instance_id"] = f"{obj.id}|{instance_uuid}"
            data["label"] = self._define_label(obj, data["productName"])

            # Add instance
            created_instance = CreatedInstance.from_existing(
                data,
                self,
                transient_data={"instance_node": obj}
            )
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
                instance_uuid = self._get_uuid_from_instance_id(instance.id)
                instances_by_uuid = lib.read(node,
                                             key=INSTANCES_DATA_KEY) or {}
                instances_by_uuid.pop(instance_uuid, None)
                if not instances_by_uuid:
                    # Remove the node, because it was the last imprinted value
                    session = node.session
                    session.removeNode(node)
                else:
                    # Update the node's imprinted value by removing the entry
                    lib.imprint(
                        node,
                        instances_by_uuid,
                        key=INSTANCES_DATA_KEY)

            # Remove the collected CreatedInstance to remove from UI directly
            self._remove_instance_from_context(instance)

    def _imprint(self, node, data):
        data.pop("label", None)  # do not store the label
        # Do not store instance id since it's the Silhouette node id
        instance_id = data.pop("instance_id")

        instance_uuid = self._get_uuid_from_instance_id(instance_id)
        instances_by_uuid = lib.read(node, key=INSTANCES_DATA_KEY) or {}
        instances_by_uuid[instance_uuid] = data
        lib.imprint(node, instances_by_uuid, key=INSTANCES_DATA_KEY)

    def _get_uuid_from_instance_id(self, instance_id: str) -> str:
        """Return uuid for instance's key on the node data from instance id."""
        return instance_id.rsplit("|", 1)[-1]

    def _define_label(self, obj: fx.Node, product_name: str) -> str:
        return f"{product_name} ({obj.label})"

    def get_pre_create_attr_defs(self):
        return [
            BoolDef("use_selection",
                    label="Use selection",
                    default=True)
        ]

    def _connect_input_to_first_matching_candidate(self, node, candidates):
        """Connect the primary input of `node` to the first candidate with
        an output that has a matching data type."""
        primary_input = node.primaryInput
        if not primary_input:
            return

        allowed_types = set(primary_input.dataTypes)
        for candidate in candidates:
            for output in candidate.outputs:
                if allowed_types.intersection(output.dataTypes):
                    output.connect(primary_input)
                    return


class SilhouetteLoader(LoaderPlugin):
    settings_category = "silhouette"
    hosts = ["silhouette"]
