from ayon_core.pipeline.workfile.workfile_template_builder import (
    LoadPlaceholderItem,
    PlaceholderLoadMixin,
)
from ayon_silhouette.api.workfile_template_builder import (
    SilhouettePlaceholderPlugin
)


class SilhouettePlaceholderLoadPlugin(SilhouettePlaceholderPlugin,
                                PlaceholderLoadMixin):
    identifier = "silhouette.placeholder.load"
    label = "Silhouette load"
    item_class = LoadPlaceholderItem

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
        pass
