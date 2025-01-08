from django import forms
from .models import Project
import pandas as pd

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'input_dataframe', 'param_file']


class ParamForm(forms.Form):
    def tdf_choice(self):
        observation_date_column = self.request.GET.get(
            'observation_date_column')
        if not observation_date_column:
            observation_date_column = self.fields['observation_date_column'].initial

        observation_date_column_values = self.df.get(observation_date_column)
        choices = list(zip(observation_date_column_values,
                       observation_date_column_values))

        return choices

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(ParamForm, self).__init__(*args, **kwargs)

        project = Project.objects.get(
            user=self.request.user, name="hello")  # hard-coded name
        self.df = pd.read_csv(project.input_dataframe)
        columns = list(self.df.columns)
        columns_choices = list(zip(columns, columns))

        self.fields['criterion_column'] = forms.ChoiceField(
            choices=columns_choices)
        self.fields['observation_date_column'] = forms.ChoiceField(
            choices=columns_choices, initial=columns[0])
        self.fields['secondary_criterion_columns'] = forms.ChoiceField(
            choices=columns_choices)
        self.fields['t1df'] = forms.ChoiceField(
            choices=self.tdf_choice)
        self.fields['t2df'] = forms.ChoiceField(
            choices=self.tdf_choice)
        self.fields['t3df'] = forms.ChoiceField(
            choices=self.tdf_choice)
        self.fields['periods_to_exclude'] = forms.MultipleChoiceField(
        choices=self.tdf_choice,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Periods to exclude"
    )
        self.fields['columns_to_exclude'] = forms.MultipleChoiceField(
        choices=columns_choices,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Columns to exclude"
    )
        self.fields['optimal_binning_columns'] = forms.MultipleChoiceField(
        choices=columns_choices,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Optimal binning columns"
    )
