import itertools
from typing import List, Dict

from ayon_core.pipeline import registered_host
from ayon_core.pipeline.workfile.workfile_template_builder import (
    AbstractTemplateBuilder,
    PlaceholderPlugin,
    PlaceholderItem
)
from ayon_core.tools.workfile_template_build import (
    WorkfileBuildPlaceholderDialog,
)
from . import lib
from .lib import (
    imprint,
    read,
    get_main_window,
    reset_session_settings
)

import fx

PLACEHOLDER_SET = "PLACEHOLDERS_SET"


class SilhouetteTemplateBuilder(AbstractTemplateBuilder):
    """Concrete implementation of AbstractTemplateBuilder for Silhouette"""

    def import_template(self, path):
        """Import template into current scene.
        Block if a template is already loaded.

        Args:
            path (str): A path to current template (usually given by
            get_template_preset implementation)

        Returns:
            bool: Whether the template was successfully imported or not
        """

        # TODO check if the template is already imported
        _objects = fx.importObjects(path)
        # TODO: Do we need to do something with the object list

        # Clear any selection if it occurred on load or import
        fx.select([])

        return True


class SilhouettePlaceholderPlugin(PlaceholderPlugin):
    node_type = "NullNode"
    data_key = "ayon.placeholder"
    item_class = PlaceholderItem

    def _create_placeholder_node(self, placeholder_data, session):
        # Create node
        placeholder_node = fx.Node(self.node_type)
        placeholder_node.label = "PLACEHOLDER"
        session.addNode(placeholder_node)
        lib.set_new_node_position(placeholder_node)
        return placeholder_node

    @lib.undo_chunk("Create placeholder")
    def create_placeholder(self, placeholder_data) -> PlaceholderItem:
        session = fx.activeSession()
        if not session:
            raise RuntimeError("Must have active session.")

        placeholder_data["plugin_identifier"] = self.identifier

        placeholder_node = self._create_placeholder_node(
            placeholder_data, session)

        fx.activate(placeholder_node)

        imprint(placeholder_node, placeholder_data, key=self.data_key)

        item = self.item_class(
            scene_identifier=placeholder_node.id,
            data=placeholder_data,
            plugin=self
        )
        # Add transient data for easier access
        item.transient_data = {
            "node": placeholder_node
        }

        return item

    @lib.undo_chunk("Update placeholder")
    def update_placeholder(self,
                           placeholder_item: PlaceholderItem,
                           placeholder_data: dict):
        node = placeholder_item.transient_data["node"]  # noqa
        placeholder_data["plugin_identifier"] = self.identifier
        imprint(node, placeholder_data, key=self.data_key)

    def _collect_placeholder_nodes(self) -> Dict[str, List[fx.Node]]:
        nodes = self.builder.get_shared_populate_data("placeholder_nodes")
        if nodes is None:
            # Populate cache
            session = fx.activeSession()
            project = fx.activeProject()
            nodes_by_plugin_identifier = {}
            for node in itertools.chain(session.nodes, project.sources):
                node_data = read(node, key=self.data_key)
                if not node_data:
                    continue

                plugin_identifier = node_data.get("plugin_identifier")
                if not plugin_identifier:
                    continue

                nodes_by_plugin_identifier.setdefault(
                    plugin_identifier, []).append(node)

            nodes = nodes_by_plugin_identifier
            self.builder.set_shared_populate_data("placeholder_nodes",
                                                  nodes_by_plugin_identifier)

        return nodes

    def collect_placeholders(self) -> List[PlaceholderItem]:
        nodes_by_identifier = self._collect_placeholder_nodes()

        placeholder_items = []
        for node in nodes_by_identifier.get(self.identifier, []):
            data = self._parse_placeholder_node_data(node)
            placeholder_item = self.item_class(
                scene_identifier=node.id,
                data=data,
                plugin=self)

            # Add transient data for easier access
            placeholder_item.transient_data = {
                "node": node
            }
            placeholder_items.append(placeholder_item)

        return placeholder_items

    def _parse_placeholder_node_data(self, node) -> dict:
        return read(node, key=self.data_key)

    @lib.undo_chunk("Delete placeholder")
    def delete_placeholder(self, placeholder: PlaceholderItem):
        """Remove placeholder if building was successful"""
        node = placeholder.transient_data["node"]  # noqa
        session = node.session
        session.removeNode(node)


@lib.undo_chunk("Build workfile template")
def build_workfile_template(*args, **kwargs):
    builder = SilhouetteTemplateBuilder(registered_host())
    builder.build_template(*args, **kwargs)

    # set all session settings to shot context default
    session = fx.activeSession()
    if session:
        reset_session_settings(session)


@lib.undo_chunk("Update workfile template")
def update_workfile_template(*args):
    builder = SilhouetteTemplateBuilder(registered_host())
    builder.rebuild_template()


def create_placeholder(*args):
    host = registered_host()
    builder = SilhouetteTemplateBuilder(host)
    window = WorkfileBuildPlaceholderDialog(host, builder,
                                            parent=get_main_window())
    window.show()


def update_placeholder(*args):
    host = registered_host()
    builder = SilhouetteTemplateBuilder(host)

    selection = fx.selection()
    if not selection:
        raise ValueError("No active selection")

    all_placeholder_items: List[PlaceholderItem] = builder.get_placeholders()
    placeholder_items_by_node_id = {
        placeholder.scene_identifier: placeholder
        for placeholder in all_placeholder_items
    }

    # Get selected placeholder items
    placeholder_items = []
    for node in selection:
        placeholder_item = placeholder_items_by_node_id.get(node.id)
        if placeholder_item:
            placeholder_items.append(placeholder_item)

    if len(placeholder_items) == 0:
        raise ValueError("No placeholder selected")
    elif len(placeholder_items) > 1:
        raise ValueError("Too many placeholders selected. Select one.")

    placeholder_item = placeholder_items[0]
    window = WorkfileBuildPlaceholderDialog(host, builder,
                                            parent=get_main_window())
    window.set_update_mode(placeholder_item)
    window.exec_()
