import ayon_api
from ayon_core.pipeline import CreatedInstance, AutoCreator, AYON_INSTANCE_ID

from ayon_silhouette.api import lib

import fx


class CreateWorkfile(AutoCreator):
    """Workfile auto-creator."""
    identifier = "io.ayon.creators.silhouette.workfile"
    label = "Workfile"
    product_type = "workfile"
    icon = "fa5.file"

    project_property_name = "AYON_workfile"

    def create(self):
        """Create workfile instances."""
        workfile_instance = next(
            (
                instance for instance in self.create_context.instances
                if instance.creator_identifier == self.identifier
            ),
            None,
        )

        project_name = self.project_name
        folder_path = self.create_context.get_current_folder_path()
        task_name = self.create_context.get_current_task_name()
        host_name = self.create_context.host_name

        existing_folder_path = None
        if workfile_instance is not None:
            existing_folder_path = workfile_instance.get("folderPath")

        if not workfile_instance:
            folder_entity = ayon_api.get_folder_by_path(
                project_name, folder_path
            )
            task_entity = ayon_api.get_task_by_name(
                project_name, folder_entity["id"], task_name
            )
            product_name = self.get_product_name(
                project_name,
                folder_entity,
                task_entity,
                task_name,
                host_name,
            )
            data = {
                "folderPath": folder_path,
                "task": task_name,
                "variant": task_name,
            }

            # Enforce forward compatibility to avoid the instance to default
            # to the legacy `AVALON_INSTANCE_ID`
            data["id"] = AYON_INSTANCE_ID

            data.update(
                self.get_dynamic_data(
                    project_name,
                    folder_entity,
                    task_entity,
                    task_name,
                    host_name,
                    workfile_instance,
                )
            )
            self.log.info("Auto-creating workfile instance...")
            workfile_instance = CreatedInstance(
                self.product_type, product_name, data, self
            )
            self._add_instance_to_context(workfile_instance)

        elif (
            existing_folder_path != folder_path
            or workfile_instance["task"] != task_name
        ):
            # Update instance context if it's different
            folder_entity = ayon_api.get_folder_by_path(
                project_name, folder_path
            )
            task_entity = ayon_api.get_task_by_name(
                project_name, folder_entity["id"], task_name
            )
            product_name = self.get_product_name(
                project_name,
                folder_entity,
                task_entity,
                self.default_variant,
                host_name,
            )

            workfile_instance["folderPath"] = folder_path
            workfile_instance["task"] = task_name
            workfile_instance["productName"] = product_name

    def collect_instances(self):

        project = fx.activeProject()
        if not project:
            return

        data = lib.read(project, key=self.project_property_name)
        if not data:
            return

        data["instance_id"] = project.id + "_workfile"

        # Add instance
        created_instance = CreatedInstance.from_existing(data, self)

        # Collect transient data
        created_instance.transient_data["project"] = project

        # Add instance to create context
        self._add_instance_to_context(created_instance)

    def update_instances(self, update_list):

        project = fx.activeProject()
        if not project:
            return

        for created_inst, _changes in update_list:
            new_data = created_inst.data_to_store()
            new_data.pop("instance_id", None)
            lib.imprint(project, new_data, key=self.project_property_name)

    def remove_instances(self, instances):
        for instance in instances:
            project = instance.transient_data["project"]
            lib.imprint(project, data=None, key=self.project_property_name)
            self._remove_instance_from_context(instance)
