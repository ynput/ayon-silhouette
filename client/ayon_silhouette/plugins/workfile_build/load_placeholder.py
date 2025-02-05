import fx

from ayon_core.pipeline.workfile.workfile_template_builder import (
    LoadPlaceholderItem,
    PlaceholderLoadMixin,
)

from ayon_silhouette.api import lib
from ayon_silhouette.api.workfile_template_builder import (
    SilhouettePlaceholderPlugin
)


class SilhouettePlaceholderLoadPlugin(
    SilhouettePlaceholderPlugin,
    PlaceholderLoadMixin):
    identifier = "silhouette.placeholder.load"
    label = "Silhouette load"
    item_class = LoadPlaceholderItem

    def _create_placeholder_node(self, placeholder_data, session):
        if placeholder_data["loader"] == "SourceLoader":
            # Special case for source loader because we want to create
            # the placeholder entry in Sources, not as a Node
            project = fx.activeProject()

            # Add Source item to the project
            source = fx.Source("")

            # Provide a nice label indicating the product
            source.label = "Placeholder"
            project.addItem(source)
            return source

        return super()._create_placeholder_node(placeholder_data, session)

    def populate_placeholder(self, placeholder):
        self.populate_load_placeholder(placeholder)

    def repopulate_placeholder(self, placeholder):
        ignore_repre_ids = {
            container["representation"]
            for container in self.builder.host.get_containers()
        }
        self.populate_load_placeholder(placeholder, ignore_repre_ids)

    def get_placeholder_options(self, options=None):
        return self.get_load_plugin_options(options)

    def _before_placeholder_load(self, placeholder):
        containers = list(self.builder.host.get_containers())
        placeholder.data["init_containers"] = containers

    def post_placeholder_process(self, placeholder, failed):

        # Get loaded nodes from the loaded representation
        containers = list(self.builder.host.get_containers())
        loaded_containers = [
            container for container in containers
            if container not in placeholder.data["init_containers"]
        ]
        loaded_items = [
            container.get("_item") for container in loaded_containers
        ]

        # Transfer connections from placeholder to loaded representation(s)
        # Note: When a single node placeholder turns into multiple nodes then
        #  the output connections are copied only to the first because the
        #  destination can only be connected once.
        node = placeholder.transient_data["node"]
        if isinstance(node, fx.Node):
            # Use the loaded node as a replacement
            # TODO: Support 'load into existing placeholder' node or alike to
            #   support single placeholder to have multiple load placeholders
            #   like Matte Shapes + Track Points both loaded to one roto node.
            position = node.getState("graph.pos")
            for loaded_item in loaded_items:
                lib.transfer_connections(node, loaded_items)

                # Try to match the node position with the placeholder
                loaded_item.setState("graph.pos", position)

        elif isinstance(node, fx.Source):
            # Clone dependency nodes of the source node in the graph
            # (because it may be loaded multiple times from one placeholder)
            # and then replace cloned node stream sources to the loaded source
            # products + transfer node connections from the dependency in-graph
            # placeholder
            streams = ["stream.primary",
                       "stream.secondary",
                       "stream.depth"]
            for dependency in node.dependencies:
                # The 'dependency' is the input node in the session graph
                # that references the source item as a view stream.
                dependency: fx.Node

                # Create a clone for every loaded item
                for loaded_item in loaded_items:
                    clone = dependency.clone()
                    dependency.parent.addNode(clone)

                    # match label with loaded source item
                    clone.label = loaded_item.label

                    # Update the streams to use the new loaded source
                    for stream in streams:
                        stream_property = clone.property(stream)
                        if stream_property is None:
                            self.log.warning(
                                f"Node {node} has no stream property: {stream}")
                            continue

                        # If the stream references the placeholder source item
                        # then remap it to the loaded item
                        if stream_property.value == node:
                            stream_property.value = loaded_item

                    lib.transfer_connections(dependency, clone)

        if not placeholder.data.get("keep_placeholder", True):

            if isinstance(node, fx.Source):
                project = fx.activeProject()
                # Delete all placeholder dependencies in the graph
                for dependency in node.dependencies:
                    project.removeItem(dependency)

            self.delete_placeholder(placeholder)