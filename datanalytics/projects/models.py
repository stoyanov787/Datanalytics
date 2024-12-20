from django.db import models
from users.models import CustomUser
from django.core.validators import FileExtensionValidator
from os.path import join

def get_input_dataframe_file_name(instance, filename):
    return join(instance.user.get_username(), instance.name, 'input_data', instance.name, 'input.csv')

def get_param_file_name(instance, filename):
    return join(instance.user.get_username(), instance.name, 'params', f'param_{instance.name}.json')

def get_param_file_name():
    return join('default_files', 'param.json')


class Project(models.Model):
    name = models.CharField(max_length=150)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    input_dataframe = models.FileField(upload_to=get_input_dataframe_file_name, validators=[FileExtensionValidator(["csv"])])
    param_file = models.FileField(upload_to=get_param_file_name, default=get_param_file_name)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'user'], name="unique_project")
        ]
