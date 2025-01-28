from ayon_core.pipeline.workfile.workfile_template_builder import (
    CreatePlaceholderItem,
    PlaceholderCreateMixin,
)

from ayon_silhouette.api.workfile_template_builder import (
    SilhouettePlaceholderPlugin
)


class SilhouettePlaceholderCreatePlugin(
    SilhouettePlaceholderPlugin, PlaceholderCreateMixin
):
    identifier = "silhouette.placeholder.create"
    label = "Silhouette create"

    item_class = CreatePlaceholderItem

    def populate_placeholder(self, placeholder):
        self.populate_create_placeholder(placeholder)

    def repopulate_placeholder(self, placeholder):
        self.populate_create_placeholder(placeholder)

    def get_placeholder_options(self, options=None):
        return self.get_create_plugin_options(options)

    def post_placeholder_process(self, placeholder, failed):
        """Cleanup placeholder after load of its corresponding representations.

        Args:
            placeholder (PlaceholderItem): Item which was just used to load
                representation.
            failed (bool): Loading of representation failed.
        """
        pass
