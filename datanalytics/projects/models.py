from django.db import models
from users.models import CustomUser
from django.core.validators import FileExtensionValidator
from os.path import join

def get_project_file_name(instance):
    return instance.user.get_username() + "_" + instance.name

def get_input_dataframe_file_name(instance, filename):
    return join("input_data", get_project_file_name(instance), 'input.csv')

def get_param_file_name(instance, filename):
    return join('params', f'params_{get_project_file_name(instance)}.json')

def get_prep_output_path(instance, filename):
    return join('output_data', get_project_file_name(instance), filename)

def get_train_eval_output_path(instance, filename):
    return join('sessions', get_project_file_name(instance), filename)

class Project(models.Model):
    name = models.CharField(max_length=150)
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
        upload_to='reports/', 
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
        constraints = [
            models.UniqueConstraint(fields=['name', 'user'], name="unique_project")
        ]