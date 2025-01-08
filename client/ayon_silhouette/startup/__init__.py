import os

from qtpy import QtCore

from ayon_core.pipeline import install_host
from ayon_core.tools.utils import host_tools

from ayon_silhouette.api import SilhouetteHost
from ayon_silhouette.api.lib import get_main_window

# Install host
install_host(SilhouetteHost())


def _add_menu_deferred():
    parent = get_main_window()

    menu_label = os.environ.get("AYON_MENU_LABEL") or "AYON"
    menu = parent.menuBar().addMenu(menu_label)

    # TODO: Add current context label menu entry
    # TODO: Add version up menu entry

    action = menu.addAction("Create...")
    action.triggered.connect(
        lambda: host_tools.show_publisher(parent=parent,
                                          tab="create")
    )

    action = menu.addAction("Load...")
    action.triggered.connect(
        lambda: host_tools.show_loader(parent=parent, use_context=True)
    )

    action = menu.addAction("Publish...")
    action.triggered.connect(
        lambda: host_tools.show_publisher(parent=parent,
                                          tab="publish")
    )

    action = menu.addAction("Manage...")
    action.triggered.connect(
        lambda: host_tools.show_scene_inventory(parent=parent)
    )

    action = menu.addAction("Library...")
    action.triggered.connect(
        lambda: host_tools.show_library_loader(parent=parent)
    )

    menu.addSeparator()
    action = menu.addAction("Work Files...")
    action.triggered.connect(
        lambda: host_tools.show_workfiles(parent=parent)
    )


QtCore.QTimer.singleShot(0, _add_menu_deferred)
