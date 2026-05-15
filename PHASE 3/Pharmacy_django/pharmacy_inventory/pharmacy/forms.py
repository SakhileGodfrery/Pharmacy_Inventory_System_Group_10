from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

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