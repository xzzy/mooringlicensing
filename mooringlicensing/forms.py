from __future__ import unicode_literals
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from django.contrib.auth import get_user_model
from django.forms import Form, ModelForm, CharField, ValidationError, EmailField

User = get_user_model()


class LoginForm(Form):
    email = EmailField(max_length=254)

# class PersonalForm(ModelForm):
#
#     class Meta:
#         model = User
#         fields = ['first_name', 'last_name']
#
#     def __init__(self, *args, **kwargs):
#         super(ProfileForm, self).__init__(*args, **kwargs)
#         self.helper = BaseFormHelper(self)
#         self.helper.form_id = 'id_form_emailuserprofile_update'
#         self.helper.attrs = {'novalidate': ''}
#         # Define the form layout.
#         self.helper.layout = Layout(
#             'first_name', 'last_name',
#             FormActions(
#                 Submit('save', 'Save', css_class='btn-lg'),
#                 Submit('cancel', 'Cancel')
#             )
#         )
#
# class ContactForm(ModelForm):
#
#     class Meta:
#         model = User
#         fields = ['email', 'phone_number','mobile_number']
#
#     def __init__(self, *args, **kwargs):
#         super(ProfileForm, self).__init__(*args, **kwargs)
#         self.helper = BaseFormHelper(self)
#         self.helper.form_id = 'id_form_emailuserprofile_update'
#         self.helper.attrs = {'novalidate': ''}
#         # Define the form layout.
#         self.helper.layout = Layout(
#             'phone_number', 'mobile_number','email',
#             FormActions(
#                 Submit('save', 'Save', css_class='btn-lg'),
#                 Submit('cancel', 'Cancel')
#             )
#         )
#
#
# class AddressForm(ModelForm):
#
#     class Meta:
#         model = Address
#         fields = ['line1', 'line2', 'locality', 'state', 'postcode']
#
#     def __init__(self, *args, **kwargs):
#         super(AddressForm, self).__init__(*args, **kwargs)
#         self.helper = BaseFormHelper(self)
#         self.helper.form_id = 'id_form_address'
#         self.helper.attrs = {'novalidate': ''}
#         self.helper.add_input(Submit('save', 'Save', css_class='btn-lg'))
#         self.helper.add_input(Submit('cancel', 'Cancel'))