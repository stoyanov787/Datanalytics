"""Models for the projects app."""

from django.db import models
from users.models import CustomUser
from django.core.validators import FileExtensionValidator
from os.path import join

def get_project_file_name(instance) -> str:
    """Generate a unique file name for the project based on the user and project name.

    :param instance: The instance of the Project model.
    :return: A string representing the unique file name.
    """
    return instance.user.get_username() + "_" + instance.name

def get_input_dataframe_file_name(instance, filename: str) -> str:
    """Generate a file path for the input dataframe based on the project name.

    :param instance: The instance of the Project model.
    :param filename: The original file name of the uploaded file.
    :return: A string representing the file path for the input dataframe.
    """
    return join("input_data", get_project_file_name(instance), 'input.csv')

def get_param_file_name(instance, filename: str) -> str:
    """Generate a file path for the parameter file based on the project name.

    :param instance: The instance of the Project model.
    :param filename: The original file name of the uploaded file.
    :return: A string representing the file path for the parameter file.
    """
    return join("params", f"params_{get_project_file_name(instance)}.json")

def get_prep_output_path(instance, filename: str) -> str:
    """Generate a file path for the preparation output based on the project name.

    :param instance: The instance of the Project model.
    :param filename: The original file name of the uploaded file.
    :return: A string representing the file path for the preparation output.
    """
    return join("output_data", get_project_file_name(instance), filename)

def get_train_eval_output_path(instance, filename: str) -> str:
    """Generate a file path for the training/evaluation output based on the project name.

    :param instance: The instance of the Project model.
    :param filename: The original file name of the uploaded file.
    :return: A string representing the file path for the training/evaluation output.
    """
    return join("sessions", get_project_file_name(instance), filename)

class Project(models.Model):
    """Model representing a project."""

    name = models.CharField(max_length=150)
    description = models.TextField(help_text="Provide a detailed description of your project")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    input_dataframe = models.FileField(
        upload_to=get_input_dataframe_file_name, 
        validators=[FileExtensionValidator(["csv"])]
    )
    param_file = models.FileField(
        upload_to=get_param_file_name, 
        validators=[FileExtensionValidator(["json"])]
    )
    sweetviz_report = models.FileField(
        upload_to="reports/", 
        null=True, 
        blank=True
    )
    prep_output = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Path to preparation output directory"
    )
    train_eval_output = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Path to training/evaluation output directory"
    )
    
    class Meta:
        """Meta class for the Project model."""
        constraints = [
            models.UniqueConstraint(fields=["name", "user"], name="unique_project")
        ]