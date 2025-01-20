from django import forms
from .models import Project
import pandas as pd
import json
import os
from django.conf import settings

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'input_dataframe']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add helpful text
        self.fields['input_dataframe'].help_text = (
            "Upload a CSV file. Make sure it's properly formatted with consistent columns and separators."
        )

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if self.user and Project.objects.filter(name=name, user=self.user).exists():
            raise forms.ValidationError('A project with this name already exists.')
        return name

    def clean_input_dataframe(self):
        input_dataframe = self.cleaned_data.get('input_dataframe')
        if input_dataframe:
            # Read first few lines to detect file format
            try:
                chunk = input_dataframe.read(1024).decode('utf-8')
                input_dataframe.seek(0)  # Reset file pointer
                
                # Check if it looks like a CSV
                if not any(separator in chunk for separator in [',', ';', '\t']):
                    raise forms.ValidationError(
                        "The file doesn't appear to be a proper CSV. "
                        "Please make sure your file is saved as CSV and uses common separators (comma, semicolon, or tab)."
                    )

                # Try parsing with different settings
                try:
                    df = pd.read_csv(input_dataframe)
                except pd.errors.EmptyDataError:
                    raise forms.ValidationError("The uploaded CSV file is empty.")
                except pd.errors.ParserError as e:
                    # Try with different separators
                    input_dataframe.seek(0)
                    try:
                        df = pd.read_csv(input_dataframe, sep=None, engine='python')
                    except Exception:
                        raise forms.ValidationError(
                            "Unable to parse the CSV file. Common issues:<br>"
                            "• Inconsistent number of columns<br>"
                            "• Mixed separators<br>"
                            "• Special characters in column names<br>"
                            "Please check your file format and try again."
                        )

                # Validate minimum requirements
                if len(df.columns) < 2:
                    raise ValidationError(
                        "The CSV file must have at least 2 columns. "
                        "Please check your file format."
                    )

                # Check for empty column names
                if any(not col or pd.isna(col) for col in df.columns):
                    raise ValidationError(
                        "Found empty or invalid column names. "
                        "Please ensure all columns have proper headers."
                    )

                return input_dataframe

            except UnicodeDecodeError:
                raise forms.ValidationError(
                    "Unable to read the file. "
                    "Please make sure it's a properly encoded CSV file."
                )
            except Exception as e:
                raise forms.ValidationError(
                    f"Error processing the file: {str(e)}. "
                    "Please ensure you're uploading a valid CSV file."
                )

    def save(self, commit=True):
        project = super().save(commit=False)
        project.user = self.user
        if commit:
            project.save()
        return project

class ParamForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        if self.project:
            try:
                self.df = pd.read_csv(self.project.input_dataframe)
                columns = list(self.df.columns)
                columns_choices = list(zip(columns, columns))
                
                # Basic fields
                self.fields['criterion_column'] = forms.ChoiceField(
                    choices=columns_choices,
                    widget=forms.Select(attrs={'class': 'form-select'}),
                    help_text="Select the main criterion column"
                )
                
                self.fields['observation_date_column'] = forms.ChoiceField(
                    choices=columns_choices,
                    widget=forms.Select(attrs={'class': 'form-select'}),
                    help_text="Select the date column",
                    initial=columns[0]
                )
                
                self.fields['secondary_criterion_columns'] = forms.ChoiceField(
                    choices=columns_choices,
                    widget=forms.Select(attrs={'class': 'form-select'}),
                    help_text="Select secondary criterion columns"
                )
                
                # Get date values for time-based selections
                if 'observation_date_column' in self.data:
                    date_column = self.data['observation_date_column']
                else:
                    date_column = columns[0]
                    
                date_values = sorted(self.df[date_column].unique())
                date_choices = [(str(date), str(date)) for date in date_values]
                
                self.fields['t1df'] = forms.ChoiceField(
                    choices=date_choices,
                    widget=forms.Select(attrs={'class': 'form-select'}),
                    help_text="Select first time period"
                )
                
                self.fields['t2df'] = forms.ChoiceField(
                    choices=date_choices,
                    widget=forms.Select(attrs={'class': 'form-select'}),
                    help_text="Select second time period"
                )
                
                self.fields['t3df'] = forms.ChoiceField(
                    choices=date_choices,
                    widget=forms.Select(attrs={'class': 'form-select'}),
                    help_text="Select third time period"
                )
                
                self.fields['periods_to_exclude'] = forms.MultipleChoiceField(
                    choices=date_choices,
                    widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
                    required=False,
                    help_text="Select periods to exclude from analysis"
                )
                
                self.fields['columns_to_exclude'] = forms.MultipleChoiceField(
                    choices=columns_choices,
                    widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
                    required=False,
                    help_text="Select columns to exclude from analysis"
                )
                
                self.fields['optimal_binning_columns'] = forms.MultipleChoiceField(
                    choices=columns_choices,
                    widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
                    required=False,
                    help_text="Select columns for optimal binning"
                )
                
            except Exception as e:
                raise forms.ValidationError(f"Error processing CSV file: {str(e)}")

    def save(self, project):
        """Save the form data as a JSON parameter file"""
        try:
            params = {
                'criterion_column': self.cleaned_data['criterion_column'],
                'observation_date_column': self.cleaned_data['observation_date_column'],
                'secondary_criterion_columns': self.cleaned_data['secondary_criterion_columns'],
                't1df': self.cleaned_data['t1df'],
                't2df': self.cleaned_data['t2df'],
                't3df': self.cleaned_data['t3df'],
                'periods_to_exclude': list(self.cleaned_data['periods_to_exclude']),
                'columns_to_exclude': list(self.cleaned_data['columns_to_exclude']),
                'optimal_binning_columns': list(self.cleaned_data['optimal_binning_columns']),
                'missing_treatment': {"Info": "Missing"},
                'lr_features': [],
                'lr_features_to_include': [],
                'trees_features_to_include': [],
                'trees_features_to_exclude': [],
                'cut_offs': {
                    'xgb': [],
                    'lr': [],
                    'dt': [],
                    'rf': []
                },
                'under_sampling': 1,
                'main_table': 'input.csv',
                'columns_to_include': [],
                'custom_calculations': [],
                'additional_tables': []
            }

            # Create params directory if it doesn't exist
            params_dir = os.path.join(settings.MEDIA_ROOT, 'params')
            os.makedirs(params_dir, exist_ok=True)
            
            # Generate param file path
            param_filename = f'params_{project.user.get_username()}_{project.name}.json'
            param_path = os.path.join('params', param_filename)
            
            full_param_path = os.path.join(params_dir, param_filename)
            
            # Save parameters to JSON file
            with open(full_param_path, 'w') as f:
                json.dump(params, f, indent=4)
            
            # Update project model with param file path
            project.param_file.name = param_path
            project.save()
            
            return True
            
        except Exception as e:
            raise forms.ValidationError(f"Error saving parameters: {str(e)}")