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
    default_variant = "Main"

    def create(self):
        """Create workfile instances."""
        if not fx.activeProject():
            return

        workfile_instance = next(
            (
                instance for instance in self.create_context.instances
                if instance.creator_identifier == self.identifier
            ),
            None,
        )

        project_entity = self.create_context.get_current_project_entity()
        project_name = project_entity["name"]
        folder_entity = self.create_context.get_current_folder_entity()
        folder_path = folder_entity["path"]
        task_entity = self.create_context.get_current_task_entity()
        task_name = task_entity["name"]
        host_name = self.create_context.host_name

        variant = self.default_variant
        if not workfile_instance:
            product_name = self.get_product_name(
                project_name,
                folder_entity,
                task_entity,
                variant,
                host_name,
                project_entity=project_entity
            )
            data = {
                "folderPath": folder_path,
                "task": task_name,
                "variant": variant,
            }

            # Enforce forward compatibility to avoid the instance to default
            # to the legacy `AVALON_INSTANCE_ID`
            data["id"] = AYON_INSTANCE_ID

            data.update(
                self.get_dynamic_data(
                    project_name,
                    folder_entity,
                    task_entity,
                    variant,
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
            workfile_instance["folderPath"] != folder_path
            or workfile_instance["task"] != task_name
        ):
            # Update instance context if it's different
            product_name = self.get_product_name(
                project_name,
                folder_entity,
                task_entity,
                variant,
                host_name,
                instance=workfile_instance,
                project_entity=project_entity
            )

            workfile_instance["folderPath"] = folder_path
            workfile_instance["task"] = task_name
            workfile_instance["productName"] = product_name

        workfile_instance.transient_data["project"] = fx.activeProject()

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
