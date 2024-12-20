from django import forms
from .models import Project
import pandas as pd
from dynamic_forms import DynamicField, DynamicFormMixin

def t1df_choice(form):
    #print(form)
    #observation_date_column = form['observation_date_column'].value()
    #observation_date_column_values = form['df'].get(observation_date_column)
    #return list(zip(observation_date_column_values, observation_date_column_values))
    return [(form['observation_date_column'].value(), form['observation_date_column'].value())]

class ParamForm(forms.Form):
    a = 1
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super(ParamForm, self).__init__(*args, **kwargs)

        project = Project.objects.get(
            user=request.user, name="one")  # hard-coded name
        df = pd.read_csv(project.input_dataframe)
        columns = list(df.columns)
        columns_choices = list(zip(columns, columns))

        self.fields['criterion_column'] = forms.ChoiceField(
            choices=columns_choices)
        self.fields['observation_date_column'] = forms.ChoiceField(
            choices=columns_choices)
        self.fields['secondary_criterion_columns'] = forms.ChoiceField(
            choices=columns_choices)
        
        print(self.fields['observation_date_column'])
        #observation_date_column = self.get_observation_date_column_value()
        #observation_date_column_values = df.get(observation_date_column)
       # observation_date_column_values_choices = list(zip(observation_date_column_values, observation_date_column_values))
        #self.fields['t1df'] = forms.ChoiceField(
          #  choices=observation_date_column_values_choices)\
        
    def get_observation_date_column_value(self):
        if self.is_bound and self.is_valid():
            return self.cleaned_data.get('observation_date_column')
        return None
