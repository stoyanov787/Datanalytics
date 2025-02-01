from django import forms
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
import pandas as pd
import json
from .models import Project

def is_date_column(series):
    try:
        pd.to_datetime(series, format='%m/%d/%Y', errors='raise')
        return True
    except (ValueError, TypeError):
        return False


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'input_dataframe']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'rows': '4',
            'placeholder': 'Enter project description'
        })

        self.fields['input_dataframe'].help_text = (
            "Upload a CSV file. Make sure it's properly formatted with consistent columns and separators."
        )

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if self.user and Project.objects.filter(name=name, user=self.user).exists():
            raise ValidationError('A project with this name already exists.')
        return name

    def clean_input_dataframe(self):
        input_dataframe = self.cleaned_data.get('input_dataframe')
        if input_dataframe:
            try:
                # Read the first chunk to check separators
                chunk = input_dataframe.read(1024).decode('utf-8')
                input_dataframe.seek(0)
                
                if not any(separator in chunk for separator in [',', ';', '\t']):
                    raise ValidationError(
                        "The file doesn't appear to be a proper CSV. "
                        "Please ensure it uses common separators (comma, semicolon, or tab)."
                    )

                # Read the full CSV
                try:
                    df = pd.read_csv(input_dataframe)
                except pd.errors.EmptyDataError:
                    raise ValidationError("The uploaded CSV file is empty.")
                except pd.errors.ParserError:
                    input_dataframe.seek(0)
                    try:
                        df = pd.read_csv(input_dataframe, sep=None, engine='python')
                    except Exception:
                        raise ValidationError(
                            "Unable to parse the CSV file. Check for:"
                            "\n• Inconsistent number of columns"
                            "\n• Mixed separators"
                            "\n• Special characters in column names"
                        )

                # Validate date columns
                has_valid_date = False
                for column in df.columns:
                    if is_date_column(df[column]):
                        has_valid_date = True
                        break

                if not has_valid_date:
                    raise ValidationError(
                        "The CSV must contain at least one date column in MM/DD/YYYY format. "
                        "Please check your date columns and try again."
                    )

                return input_dataframe

            except UnicodeDecodeError:
                raise ValidationError("Unable to read the file. Please ensure it's a properly encoded CSV file.")
            except Exception as e:
                raise ValidationError(f"Error processing file: {str(e)}")

            except UnicodeDecodeError:
                raise ValidationError(
                    "Unable to read the file. "
                    "Please make sure it's a properly encoded CSV file."
                )
            except Exception as e:
                raise ValidationError(
                    f"Error processing the file: {str(e)}. "
                    "Please ensure you're uploading a valid CSV file."
                )

    def save(self, commit=True):
        project = super().save(commit=False)
        project.user = self.user
        if commit:
            project.save()
        return project


class DynamicCutoffField(forms.Field):
    def __init__(self, *args, **kwargs):
        kwargs['required'] = kwargs.get('required', True)
        super().__init__(*args, **kwargs)
        self.widget = forms.TextInput(attrs={
            'placeholder': '0.2, 0.4, 0.6, 0.8',
            'class': 'form-control cutoff-input'
        })

    def clean(self, value):
        if not value and self.required:
            raise forms.ValidationError("This field is required. Please enter at least one value.")
            
        if not value:
            return [0, 1]

        try:
            values = [float(x.strip()) for x in value.split(',')]
            
            invalid_values = [v for v in values if not (0 < v < 1)]
            if invalid_values:
                raise forms.ValidationError(
                    f"Values must be between 0 and 1. Invalid values: {', '.join(str(v) for v in invalid_values)}"
                )
            
            if any(values[i] >= values[i+1] for i in range(len(values)-1)):
                raise forms.ValidationError("Values must be in ascending order")
            
            values.insert(0, 0)
            values.append(1)
            
            return values
            
        except ValueError:
            raise forms.ValidationError("Please enter valid decimal numbers separated by commas")
        except Exception as e:
            raise forms.ValidationError(f"Invalid input: {str(e)}")


class ParamForm(forms.Form):
    MISSING_TREATMENT_CHOICES = [
        ("Missing", "Missing"),
        ("column_mean", "Column Mean"),
        ("median", "Median"),
        ("delete", "Delete")
    ]

    criterion_column = forms.ChoiceField(
        choices=[],
        label="Criterion Column"
    )
    observation_date_column = forms.ChoiceField(
        choices=[],
        label="Observation Date Column"
    )
    secondary_criterion_columns = forms.ChoiceField(
        choices=[],
        label="Secondary Criterion Columns"
    )
    missing_treatment = forms.ChoiceField(
        choices=MISSING_TREATMENT_CHOICES,
        initial="Missing",
        label="Missing Treatment"
    )
    t1df = forms.ChoiceField(
        choices=[],
        label="T1 Date"
    )
    t2df = forms.ChoiceField(
        choices=[],
        label="T2 Date"
    )
    t3df = forms.ChoiceField(
        choices=[],
        label="T3 Date"
    )
    periods_to_exclude = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Periods to Exclude"
    )
    columns_to_exclude = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Columns to Exclude"
    )
    optimal_binning_columns = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Optimal Binning Columns"
    )
    under_sampling = forms.FloatField(
        min_value=0,
        max_value=1,
        initial=1,
        label="Under Sampling",
        help_text="Enter a value between 0 and 1"
    )
    xgb_cutoffs = DynamicCutoffField(
        required=True,
        label="XGBoost Cutoffs",
        help_text="Enter at least one value between 0 and 1, separated by commas (e.g., 0.2, 0.4, 0.6, 0.8)"
    )
    lr_cutoffs = DynamicCutoffField(
        required=True,
        label="Logistic Regression Cutoffs",
        help_text="Enter at least one value between 0 and 1, separated by commas (e.g., 0.2, 0.4, 0.6, 0.8)"
    )
    dt_cutoffs = DynamicCutoffField(
        required=True,
        label="Decision Tree Cutoffs",
        help_text="Enter at least one value between 0 and 1, separated by commas (e.g., 0.2, 0.4, 0.6, 0.8)"
    )
    rf_cutoffs = DynamicCutoffField(
        required=True,
        label="Random Forest Cutoffs",
        help_text="Enter at least one value between 0 and 1, separated by commas (e.g., 0.2, 0.4, 0.6, 0.8)"
    )

    def __init__(self, *args, project=None, **kwargs):
        super(ParamForm, self).__init__(*args, **kwargs)
        if project:
            self.project = project
            self.df = pd.read_csv(project.input_dataframe)
            
            date_columns = [col for col in self.df.columns if is_date_column(self.df[col])]
            
            columns = list(self.df.columns)
            columns_choices = list(zip(columns, columns))
            date_columns_choices = list(zip(date_columns, date_columns))

            self.fields['criterion_column'].choices = columns_choices
            self.fields['observation_date_column'].choices = date_columns_choices
            self.fields['secondary_criterion_columns'].choices = columns_choices
            self.fields['columns_to_exclude'].choices = columns_choices
            self.fields['optimal_binning_columns'].choices = columns_choices

            # Set initial date-related fields
            if date_columns:
                # If form is being submitted, use the selected observation date
                if self.data and self.data.get('observation_date_column'):
                    date_column = self.data.get('observation_date_column')
                else:
                    # On initial load, use the first date column
                    date_column = date_columns[0]

                dates = pd.to_datetime(self.df[date_column].unique())
                dates = sorted(dates)
                formatted_dates = [d.strftime('%m/%d/%Y') for d in dates]
                date_choices = list(zip(formatted_dates, formatted_dates))
                
                self.fields['t1df'].choices = date_choices
                self.fields['t2df'].choices = date_choices
                self.fields['t3df'].choices = date_choices
                self.fields['periods_to_exclude'].choices = date_choices

                # Set default values for t1df, t2df, t3df
                if not self.data:  # Only set defaults on initial load
                    if formatted_dates:
                        self.fields['t1df'].initial = formatted_dates[0]
                        self.fields['t2df'].initial = formatted_dates[len(formatted_dates)//2]
                        self.fields['t3df'].initial = formatted_dates[-1]

    def clean(self):
        cleaned_data = super().clean()
        
        criterion = cleaned_data.get('criterion_column')
        secondary = cleaned_data.get('secondary_criterion_columns')
        obs_date_col = cleaned_data.get('observation_date_column')
        
        # Validate criterion columns are different
        if criterion and secondary and criterion == secondary:
            self.add_error('secondary_criterion_columns', 
                          "Secondary criterion column cannot be the same as primary criterion")

        # Validate key columns are not excluded
        columns_to_exclude = cleaned_data.get('columns_to_exclude', [])
        key_columns = [criterion, obs_date_col, secondary]
        
        for col in key_columns:
            if col and col in columns_to_exclude:
                self.add_error('columns_to_exclude',
                             f"Cannot exclude key column: {col}")

        # Validate date column and time periods
        if obs_date_col and self.df is not None:
            try:
                date_series = pd.to_datetime(self.df[obs_date_col], errors='raise')
                if date_series.isna().any():
                    self.add_error('observation_date_column',
                                 "Column contains invalid dates.")

                # Validate time period order
                t1df = cleaned_data.get('t1df')
                t2df = cleaned_data.get('t2df')
                t3df = cleaned_data.get('t3df')
                
                if all([t1df, t2df, t3df]):
                    dates = [pd.to_datetime(d) for d in [t1df, t2df, t3df]]
                    if not (dates[0] <= dates[1] <= dates[2]):
                        self.add_error(None, 
                                     "Time periods must be in chronological order (T1 ≤ T2 ≤ T3)")

                # Validate periods to exclude
                periods = cleaned_data.get('periods_to_exclude', [])
                for period in periods:
                    try:
                        pd.to_datetime(period)
                    except (ValueError, TypeError):
                        self.add_error('periods_to_exclude',
                                     f"Invalid date: {period}")

            except (ValueError, TypeError):
                self.add_error('observation_date_column',
                             "Selected column must contain valid dates (e.g., YYYY-MM-DD)")

        return cleaned_data

    def save(self, project):
        cleaned_data = self.cleaned_data
        params = {
            "criterion_column": cleaned_data['criterion_column'],
            "missing_treatment": cleaned_data['missing_treatment'],
            "observation_date_column": cleaned_data['observation_date_column'],
            "secondary_criterion_columns": cleaned_data['secondary_criterion_columns'],
            "t1df": cleaned_data['t1df'],
            "t2df": cleaned_data['t2df'],
            "t3df": cleaned_data['t3df'],
            "periods_to_exclude": list(cleaned_data.get('periods_to_exclude', [])),
            "columns_to_exclude": list(cleaned_data.get('columns_to_exclude', [])),
            "lr_features": [],
            "lr_features_to_include": [],
            "trees_features_to_include": [],
            "trees_features_to_exclude": [],
            "cut_offs": {
                "xgb": cleaned_data['xgb_cutoffs'],
                "lr": cleaned_data['lr_cutoffs'],
                "dt": cleaned_data['dt_cutoffs'],
                "rf": cleaned_data['rf_cutoffs']
            },
            "under_sampling": cleaned_data['under_sampling'],
            "optimal_binning_columns": list(cleaned_data.get('optimal_binning_columns', [])),
            "main_table": "input.csv",
            "columns_to_include": [],
            "custom_calculations": [],
            "additional_tables": []
        }

        json_content = json.dumps(params, indent=4)
        project.param_file.save(
            f'params_{project.user.get_username()}_{project.name}.json',
            ContentFile(json_content.encode('utf-8'))
        )