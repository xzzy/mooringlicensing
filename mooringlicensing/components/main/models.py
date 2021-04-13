from __future__ import unicode_literals
import os

from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_delete
from django.utils.encoding import python_2_unicode_compatible
from django.core.exceptions import ValidationError
from ledger.accounts.models import EmailUser, RevisionedMixin
from django.contrib.postgres.fields.jsonb import JSONField
from datetime import datetime


class UserSystemSettings(models.Model):
    user = models.OneToOneField(EmailUser, related_name='system_settings')

    class Meta:
        app_label = 'mooringlicensing'
        verbose_name_plural = "User System Settings"


@python_2_unicode_compatible
class UserAction(models.Model):
    who = models.ForeignKey(EmailUser, null=False, blank=False)
    when = models.DateTimeField(null=False, blank=False, auto_now_add=True)
    what = models.TextField(blank=False)

    def __str__(self):
        return "{what} ({who} at {when})".format(
            what=self.what,
            who=self.who,
            when=self.when
        )

    class Meta:
        abstract = True
        app_label = 'mooringlicensing'


class CommunicationsLogEntry(models.Model):
    TYPE_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone Call'),
        ('mail', 'Mail'),
        ('person', 'In Person'),
        ('onhold', 'On Hold'),
        ('onhold_remove', 'Remove On Hold'),
        ('with_qaofficer', 'With QA Officer'),
        ('with_qaofficer_completed', 'QA Officer Completed'),
        ('referral_complete','Referral Completed'),
    ]
    DEFAULT_TYPE = TYPE_CHOICES[0][0]

    to = models.TextField(blank=True, verbose_name="To")
    fromm = models.CharField(max_length=200, blank=True, verbose_name="From")
    cc = models.TextField(blank=True, verbose_name="cc")

    type = models.CharField(max_length=35, choices=TYPE_CHOICES, default=DEFAULT_TYPE)
    reference = models.CharField(max_length=100, blank=True)
    subject = models.CharField(max_length=200, blank=True, verbose_name="Subject / Description")
    text = models.TextField(blank=True)

    customer = models.ForeignKey(EmailUser, null=True, related_name='+')
    staff = models.ForeignKey(EmailUser, null=True, related_name='+')

    created = models.DateTimeField(auto_now_add=True, null=False, blank=False)

    class Meta:
        app_label = 'mooringlicensing'


@python_2_unicode_compatible
class Document(models.Model):
    name = models.CharField(max_length=255, blank=True,
                            verbose_name='name', help_text='')
    description = models.TextField(blank=True,
                                   verbose_name='description', help_text='')
    uploaded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'mooringlicensing'
        abstract = True

    @property
    def path(self):
        #comment above line to fix the error "The '_file' attribute has no file associated with it." when adding comms log entry.
        if self._file:
            return self._file.path
        else:
            return ''

    @property
    def filename(self):
        return os.path.basename(self.path)

    def __str__(self):
        return self.name or self.filename


class ApplicationType(models.Model):
    code = models.CharField(max_length=30, blank=True, null=True, unique=True)
    description = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return 'id:{}({}) {}'.format(self.id, self.code, self.description)

    class Meta:
        app_label = 'mooringlicensing'



#@python_2_unicode_compatible
#class ApplicationType(models.Model):
#    WL = 'Waiting List Application'
#    AA = 'Annual Admission Application'
#    AU = 'Authorised User Application'
#    ML = 'Mooring License Application'
#
#    APPLICATION_TYPES = (
#        (WL, 'Waiting List Application'),
#        (AA, 'Annual Admission Application'),
#        (AU, 'Authorised User Application'),
#        (ML, 'Mooring License Application'),
#    )
#
#    # name = models.CharField(max_length=64, unique=True)
#    name = models.CharField(
#        verbose_name='Application Type name',
#        max_length=64,
#        choices=APPLICATION_TYPES,
#    )
#    order = models.PositiveSmallIntegerField(default=0)
#    visible = models.BooleanField(default=True)
#    application_fee = models.DecimalField(max_digits=6, decimal_places=2)
#    oracle_code_application = models.CharField(max_length=50)
#    is_gst_exempt = models.BooleanField(default=True)
#    #domain_used = models.CharField(max_length=40, choices=DOMAIN_USED_CHOICES, default=DOMAIN_USED_CHOICES[0][0])
#
#    class Meta:
#        ordering = ['order', 'name']
#        app_label = 'mooringlicensing'
#
#    def __str__(self):
#        return self.name
#
#    @property
#    def acronym(self):
#        if self.name:
#            return self.name[0]


class Question(models.Model):
    CORRECT_ANSWER_CHOICES = (
        ('answer_one', 'Answer one'), ('answer_two', 'Answer two'), ('answer_three', 'Answer three'),
        ('answer_four', 'Answer four'))
    question_text = models.TextField(blank=False)
    answer_one = models.CharField(max_length=200, blank=True)
    answer_two = models.CharField(max_length=200, blank=True)
    answer_three = models.CharField(max_length=200, blank=True)
    answer_four = models.CharField(max_length=200, blank=True)
    #answer_five = models.CharField(max_length=200, blank=True)
    correct_answer = models.CharField('Correct Answer', max_length=40, choices=CORRECT_ANSWER_CHOICES,
                                       default=CORRECT_ANSWER_CHOICES[0][0])
    #application_type = models.ForeignKey(ApplicationType, null=True, blank=True)

    class Meta:
        #ordering = ['name']
        app_label = 'mooringlicensing'

    def __str__(self):
        return self.question_text

    @property
    def correct_answer_value(self):
        return getattr(self, self.correct_answer)


class GlobalSettings(models.Model):
    keys = (
        ('', ''),
        #('credit_facility_link', 'Credit Facility Link'),
        #('deed_poll', 'Deed poll'),
        #('deed_poll_filming', 'Deed poll Filming'),
        #('deed_poll_event', 'Deed poll Event'),
        #('online_training_document', 'Online Training Document'),
        #('park_finder_link', 'Park Finder Link'),
        #('fees_and_charges', 'Fees and charges link'),
        #('commercial_filming_handbook', 'Commercial Filming Handbook link'),
        #('park_stay_link', 'Park Stay Link'),
        #('event_traffic_code_of_practice', 'Event traffic code of practice'),
        #('trail_section_map', 'Trail section map'),
        #('dwer_application_form', 'DWER Application Form'),

    )
    key = models.CharField(max_length=255, choices=keys, blank=False, null=False,)
    value = models.CharField(max_length=255)

    class Meta:
        app_label = 'mooringlicensing'
        verbose_name_plural = "Global Settings"


#def update_mooringlicensing_word_filename(instance, filename):
#    cur_time = datetime.now().strftime('%Y%m%d_%H_%M') 
#    new_filename = 'fee_waiver_template_{}'.format(cur_time)
#    return 'mooringlicensing_template/{}.docx'.format(new_filename)
#
#
#class FeeWaiverWordTemplate(models.Model):
#    _file = models.FileField(upload_to=update_mooringlicensing_word_filename, max_length=255)
#    uploaded_date = models.DateTimeField(auto_now_add=True, editable=False)
#    description = models.TextField(blank=True,
#                                   verbose_name='description', help_text='')
#
#    class Meta:
#        app_label = 'mooringlicensing'
#        verbose_name_plural = 'Fee Waiver Templates'
#        ordering = ['-id']
#
#    def __str__(self):
#        return "Version: {}, {}".format(self.id, self._file.name)


@python_2_unicode_compatible
class SystemMaintenance(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def duration(self):
        """ Duration of system maintenance (in mins) """
        return int( (self.end_date - self.start_date).total_seconds()/60.) if self.end_date and self.start_date else ''
    duration.short_description = 'Duration (mins)'

    class Meta:
        app_label = 'mooringlicensing'
        verbose_name_plural = "System maintenance"

    def __str__(self):
        return 'System Maintenance: {} ({}) - starting {}, ending {}'.format(self.name, self.description, self.start_date, self.end_date)

# Not currently used
class TemporaryDocumentCollection(models.Model):

    class Meta:
        app_label = 'mooringlicensing'


# Not currently used
class TemporaryDocument(Document):
    temp_document_collection = models.ForeignKey(
        TemporaryDocumentCollection,
        related_name='documents')
    _file = models.FileField(max_length=255)

    class Meta:
        app_label = 'mooringlicensing'


def update_electoral_roll_doc_filename(instance, filename):
    return '{}/emailusers/{}/documents/{}'.format(settings.MEDIA_APP_DIR, instance.emailuser.id,filename)


class VesselSizeCategoryGroup(RevisionedMixin):
    name = models.CharField(max_length=100, null=False, blank=False)
    # created = models.DateTimeField(auto_now_add=True)
    # updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        num_item = self.vessel_size_categories.count()
        return '{} ({} category)'.format(self.name, num_item) if num_item == 1 else '{} ({} categories)'.format(self.name, num_item)

    class Meta:
        verbose_name_plural = "Vessel Size Category Group"
        app_label = 'mooringlicensing'

    @property
    def is_editable(self):
        for fee_constructor in self.fee_constructors.all():
            if fee_constructor.num_of_times_used_for_payment:
                # This season has been used in the fee_constructor for payments at least once
                return False
        return True

class VesselSizeCategory(RevisionedMixin):
    name = models.CharField(max_length=100)
    start_size = models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    include_start_size = models.BooleanField(default=True)  # When true, 'start_size' is included.
    vessel_size_category_group = models.ForeignKey(VesselSizeCategoryGroup, null=True, blank=True, related_name='vessel_size_categories')
    # created = models.DateTimeField(auto_now_add=True)
    # updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Vessel Size Categories"
        app_label = 'mooringlicensing'




#import reversion
#reversion.register(UserAction)
#reversion.register(CommunicationsLogEntry)
#reversion.register(Document)
#reversion.register(SystemMaintenance)


