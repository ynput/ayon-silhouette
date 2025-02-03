from ayon_core.pipeline.workfile.workfile_template_builder import (
    LoadPlaceholderItem,
    PlaceholderLoadMixin,
)

import fx

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

    def post_placeholder_process(self, placeholder, failed):
        """Cleanup placeholder after load of its corresponding representations.

        Args:
            placeholder (PlaceholderItem): Item which was just used to load
                representation.
            failed (bool): Loading of representation failed.
        """
        if not placeholder.data.get("keep_placeholder", True):
            self.delete_placeholder(placeholder)