from django import forms
from django.core.validators import EmailValidator
from django.db import connection

class RegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True, validators=[EmailValidator()])
    date_of_birth = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], required=False)
    country = forms.CharField(max_length=50, required=False)
    password1 = forms.CharField(widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(widget=forms.PasswordInput, required=True)

    def clean_email(self):
        email = self.cleaned_data['email']
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM users WHERE email = %s", [email])
            if cursor.fetchone():
                raise forms.ValidationError("Email already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

# Keep your other forms exactly as they were
class AddRecordForm(forms.Form):
    table_name = forms.ChoiceField(choices=[], label='Select Table')
    def __init__(self, *args, **kwargs):
        tables = kwargs.pop('tables', [])
        super().__init__(*args, **kwargs)
        if tables:
            self.fields['table_name'].choices = [(t[0], t[0]) for t in tables]

class QueryForm(forms.Form):
    QUERY_CHOICES = [
        ('1', 'Patient Prescription History'),
        ('2', 'Sales Performance by Category'),
        ('3', 'Low Stock Products'),
        ('4', 'Top 5 Best Selling Products'),
        ('5', 'Recent Transactions'),
        ('6', 'Products Sorted by Price'),
        ('7', 'Suppliers Sorted by Status'),
        ('8', 'Allergy Patients Search'),
        ('9', 'Products with Price Range'),
        ('10', 'Expiry Date Tracking'),
        ('11', 'Monthly Sales Trend'),
        ('12', 'Pharmacy Performance Metrics'),
        ('13', 'Product Performance Analysis'),
        ('14', 'Supplier Performance Evaluation'),
        ('15', 'Complete Patient Journey'),
        ('16', 'Supply Chain Analysis'),
        ('17', 'Top Performing Products'),
        ('18', 'High-Value Customers'),
        ('19', 'Expiring Batches Alert'),
        ('20', 'Custom SQL Query')
    ]
    selected_query = forms.ChoiceField(choices=QUERY_CHOICES, label='Select Pre-defined Query')
    custom_sql = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}), required=False, label='Custom SQL Query')

class UpdateRecordForm(forms.Form):
    table_name = forms.ChoiceField(choices=[], label='Select Table')
    record_id = forms.IntegerField(label='Record ID')
    update_data = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label='Update Data (JSON format)')
    def __init__(self, *args, **kwargs):
        tables = kwargs.pop('tables', [])
        super().__init__(*args, **kwargs)
        if tables:
            self.fields['table_name'].choices = [(t[0], t[0]) for t in tables]