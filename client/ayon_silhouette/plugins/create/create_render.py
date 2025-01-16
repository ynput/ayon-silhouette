from ayon_silhouette.api import (
    lib,
    plugin
)


class CreateRender(plugin.SilhouetteCreator):
    """Render Output"""

    identifier = "io.ayon.creators.silhouette.render"
    label = "Render"
    description = __doc__
    product_type = "render"
    icon = "eye"

    def create(self, product_name, instance_data, pre_create_data):

        with lib.undo_chunk("Create Render"):
            instance = super().create(
                product_name, instance_data, pre_create_data)

            # Set default render output path
            # TODO: Make this configurable in settings
            instance_node = instance.transient_data["instance_node"]
            instance_node.path.value = (
                "$(AYON_WORKDIR)/renders/silhouette/"
                f"{product_name}/{product_name}"
            )

    def get_instance_attr_defs(self):
        defs = lib.collect_animation_defs(self.create_context)
        return defs
