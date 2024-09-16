from django.conf import settings
from django.contrib import admin
from django.urls import re_path, include
from django.conf.urls.static import static
from rest_framework import routers
from django_media_serv.urls import urlpatterns as media_serv_patterns

import mooringlicensing
# import mooringlicensing.components.approvals.api
from mooringlicensing import views
from mooringlicensing.components.approvals.views import DcvAdmissionFormView
from mooringlicensing.components.payments_ml.views import ApplicationFeeView, ApplicationFeeSuccessView, InvoicePDFView, \
    DcvPermitFeeView, DcvPermitFeeSuccessView, DcvPermitPDFView, ConfirmationView, DcvAdmissionFeeView, \
    DcvAdmissionFeeSuccessView, DcvAdmissionPDFView, ApplicationFeeExistingView, StickerReplacementFeeView, \
    StickerReplacementFeeSuccessView, RefundProposalHistoryView, ProposalPaymentHistoryView, ApplicationFeeAlreadyPaid, \
    ApplicationFeeSuccessViewPreload, DcvPermitFeeSuccessViewPreload, DcvAdmissionFeeSuccessViewPreload, \
    StickerReplacementFeeSuccessViewPreload
from mooringlicensing.components.proposals import views as proposal_views
from mooringlicensing.components.organisations import views as organisation_views
from mooringlicensing.components.payments_ml import api as payments_api
from mooringlicensing.components.proposals import api as proposal_api
from mooringlicensing.components.approvals import api as approval_api
from mooringlicensing.components.compliances import api as compliances_api
from mooringlicensing.components.proposals.views import AuthorisedUserApplicationEndorseView, \
    MooringLicenceApplicationDocumentsUploadView
from mooringlicensing.components.users import api as users_api
from mooringlicensing.components.organisations import api as org_api
from mooringlicensing.components.main import api as main_api
# from ledger.urls import urlpatterns as ledger_patterns
from ledger_api_client.urls import urlpatterns as ledger_patterns

# API patterns
from mooringlicensing.management.default_data_manager import DefaultDataManager
from mooringlicensing.settings import PRIVATE_MEDIA_DIR_NAME
from mooringlicensing.utils import are_migrations_running
from django.urls import path

router = routers.DefaultRouter()
router.include_root_view = settings.DEBUG
router.register(r'organisations', org_api.OrganisationViewSet, 'organisations')
router.register(r'proposal', proposal_api.ProposalViewSet, 'proposal')
router.register(r'proposal_by_uuid', proposal_api.ProposalByUuidViewSet, 'proposal_by_uuid')
router.register(r'waitinglistapplication', proposal_api.WaitingListApplicationViewSet, 'waitinglistapplication')
router.register(r'annualadmissionapplication', proposal_api.AnnualAdmissionApplicationViewSet, 'annualadmissionapplication')
router.register(r'authoriseduserapplication', proposal_api.AuthorisedUserApplicationViewSet, 'authoriseduserapplication')

router.register(r'internalwaitinglistapplication', proposal_api.InternalWaitingListApplicationViewSet, 'internalwaitinglistapplication')
router.register(r'internalannualadmissionapplication', proposal_api.InternalAnnualAdmissionApplicationViewSet, 'internalannualadmissionapplication')
router.register(r'internalauthoriseduserapplication', proposal_api.InternalAuthorisedUserApplicationViewSet, 'internalauthoriseduserapplication')

router.register(r'mooringlicenceapplication', proposal_api.MooringLicenceApplicationViewSet, 'mooringlicenceapplication')
router.register(r'site_licensee_mooring_requests_paginated', proposal_api.SiteLicenseeMooringRequestPaginatedViewSet,'site_licensee_mooring_requests_paginated')
router.register(r'proposals_paginated', proposal_api.ProposalPaginatedViewSet, 'proposals_paginated')
router.register(r'approvals_paginated', approval_api.ApprovalPaginatedViewSet, 'approvals_paginated')
router.register(r'dcvpermits_paginated', approval_api.DcvPermitPaginatedViewSet, 'dcvpermits_paginated')
router.register(r'dcvadmissions_paginated', approval_api.DcvAdmissionPaginatedViewSet, 'dcvadmissions_paginated')
router.register(r'stickers_paginated', approval_api.StickerPaginatedViewSet, 'stickers_paginated')
router.register(r'stickers', approval_api.StickerViewSet, 'stickers')
router.register(r'compliances_paginated', compliances_api.CompliancePaginatedViewSet, 'compliances_paginated')
router.register(r'moorings_paginated', proposal_api.MooringPaginatedViewSet, 'moorings_paginated')
router.register(r'approvals', approval_api.ApprovalViewSet, 'approvals')
router.register(r'waitinglistallocation', approval_api.WaitingListAllocationViewSet, 'waitinglistallocation')
router.register(r'compliances', compliances_api.ComplianceViewSet, 'compliances')
router.register(r'proposal_requirements', proposal_api.ProposalRequirementViewSet, 'proposal_requirements')
router.register(r'proposal_standard_requirements', proposal_api.ProposalStandardRequirementViewSet, 'proposal_standard_requirements')
router.register(r'organisation_requests', org_api.OrganisationRequestsViewSet, 'organisation_requests')
router.register(r'organisation_contacts', org_api.OrganisationContactViewSet, 'organisation_contacts')
router.register(r'my_organisations', org_api.MyOrganisationsViewSet, 'my_organisations')
router.register(r'users', users_api.UserViewSet, 'users')
router.register(r'amendment_request', proposal_api.AmendmentRequestViewSet, 'amendment_request')
router.register(r'compliance_amendment_request', compliances_api.ComplianceAmendmentRequestViewSet, 'compliance_amendment_request')
router.register(r'payment', main_api.PaymentViewSet, 'payment')
router.register(r'mooringbays', proposal_api.MooringBayViewSet, 'mooringbays')
router.register(r'vessel', proposal_api.VesselViewSet, 'vessel')
router.register(r'mooring', proposal_api.MooringViewSet, 'mooring')
router.register(r'dcv_vessel', approval_api.DcvVesselViewSet, 'dcv_vessel')
router.register(r'vesselownership', proposal_api.VesselOwnershipViewSet, 'vesselownership')
router.register(r'dcv_permit', approval_api.DcvPermitViewSet, 'dcv_permit')
router.register(r'internal_dcv_permit', approval_api.InternalDcvPermitViewSet, 'internal_dcv_permit')
router.register(r'dcv_admission', approval_api.DcvAdmissionViewSet, 'dcv_admission')
router.register(r'internal_dcv_admission', approval_api.InternalDcvAdmissionViewSet, 'internal_dcv_admission')
# router.register(r'dcv_admission_external', mooringlicensing.components.approvals.api.DcvAdmissionViewSet, 'dcv_admission')
router.register(r'company', proposal_api.CompanyViewSet, 'company')
router.register(r'companyownership', proposal_api.CompanyOwnershipViewSet, 'companyownership')
router.register(r'temporary_document', main_api.TemporaryDocumentCollectionViewSet, 'temporary_document')

api_patterns = [
    re_path(r'^api/profile$', users_api.GetProfile.as_view(), name='get-profile'),
    re_path(r'^api/profile/(?P<proposal_pk>\d+)$', users_api.GetProposalApplicantUser.as_view(), name='get-proposal-applicant-user'),
    re_path(r'^api/countries$', users_api.GetCountries.as_view(), name='get-countries'),
    re_path(r'^api/filtered_organisations$', org_api.OrganisationListFilterView.as_view(), name='filtered_organisations'),
    re_path(r'^api/filtered_payments$', approval_api.ApprovalPaymentFilterViewSet.as_view(), name='filtered_payments'),
    re_path(r'^api/application_types$', proposal_api.GetApplicationTypeDescriptions.as_view(), name='get-application-type-descriptions'),
    re_path(r'^api/application_types_dict$', proposal_api.GetApplicationTypeDict.as_view(), name='get-application-type-dict'),
    re_path(r'^api/application_categories_dict$', proposal_api.GetApplicationCategoryDict.as_view(), name='get-application-category-dict'),
    re_path(r'^api/payment_system_id$', proposal_api.GetPaymentSystemId.as_view(), name='get-payment-system-id'),
    re_path(r'^api/fee_item_sticker_replacement$', proposal_api.GetStickerReplacementFeeItem.as_view(), name='get-sticker-replacement-fee-item'),
    re_path(r'^api/vessel_rego_nos$', proposal_api.GetVesselRegoNos.as_view(), name='get-vessel_rego-nos'),
    re_path(r'^api/mooring_lookup$', proposal_api.GetMooring.as_view(), name='get-mooring'),
    re_path(r'^api/mooring_lookup_by_site_licensee$', proposal_api.GetMooringBySiteLicensee.as_view(), name='get-mooring-lookup-by-site-licensee'),
    re_path(r'^api/mooring_lookup_per_bay$', proposal_api.GetMooringPerBay.as_view(), name='get-mooring-per-bay'),
    re_path(r'^api/vessel_lookup$', proposal_api.GetVessel.as_view(), name='get-vessel'),
    re_path(r'^api/sticker_lookup$', approval_api.GetSticker.as_view(), name='get-sticker'),
    re_path(r'^api/person_lookup$', users_api.GetPerson.as_view(), name='get-person'),
    re_path(r'^api/company_names$', proposal_api.GetCompanyNames.as_view(), name='get-company-names'),
    re_path(r'^api/dcv_vessel_rego_nos$', proposal_api.GetDcvVesselRegoNos.as_view(), name='get-dcv-vessel_rego-nos'),
    re_path(r'^api/dcv_organisations$', proposal_api.GetDcvOrganisations.as_view(), name='get-dcv-organisations'),
    re_path(r'^api/fee_configurations$', payments_api.GetFeeConfigurations.as_view(), name='get-fee-configurations'),
    re_path(r'^api/vessel_types_dict$', proposal_api.GetVesselTypesDict.as_view(), name='get-vessel-types-dict'),
    re_path(r'^api/insurance_choices_dict$', proposal_api.GetInsuranceChoicesDict.as_view(), name='get-insurance-choices-dict'),
    re_path(r'^api/application_statuses_dict$', proposal_api.GetApplicationStatusesDict.as_view(), name='get-application-statuses-dict'),
    re_path(r'^api/approval_types_dict$', approval_api.GetApprovalTypeDict.as_view(), name='get-approval-type-dict'),
    re_path(r'^api/wla_allowed$', approval_api.GetWlaAllowed.as_view(), name='get-wla-allowed'),
    re_path(r'^api/current_season$', approval_api.GetCurrentSeason.as_view(), name='get-current-season'),
    re_path(r'^api/approval_statuses_dict$', approval_api.GetApprovalStatusesDict.as_view(), name='get-approval-statuses-dict'),
    re_path(r'^api/fee_seasons_dict$', approval_api.GetFeeSeasonsDict.as_view(), name='get-fee-seasons-dict'),
    re_path(r'^api/sticker_status_dict$', approval_api.GetStickerStatusDict.as_view(), name='get-sticker-status-dict'),
    re_path(r'^api/daily_admission_url$', approval_api.GetDailyAdmissionUrl.as_view(), name='get-daily-admission-url'),
    re_path(r'^api/seasons_for_dcv_dict$', payments_api.GetSeasonsForDcvPermitDict.as_view(), name='get-approval-statuses-dict'),
    re_path(r'^api/compliance_statuses_dict$', compliances_api.GetComplianceStatusesDict.as_view(), name='get-compliance-statuses-dict'),
    re_path(r'^api/mooring_statuses_dict$', proposal_api.GetMooringStatusesDict.as_view(), name='get-mooring-statuses-dict'),
    re_path(r'^api/empty_list$', proposal_api.GetEmptyList.as_view(), name='get-empty-list'),
    re_path(r'^api/organisation_access_group_members',org_api.OrganisationAccessGroupMembers.as_view(),name='organisation-access-group-members'),
    re_path(r'^api/',include(router.urls)),
    re_path(r'^api/amendment_request_reason_choices',proposal_api.AmendmentRequestReasonChoicesView.as_view(),name='amendment_request_reason_choices'),
    re_path(r'^api/compliance_amendment_reason_choices',compliances_api.ComplianceAmendmentReasonChoicesView.as_view(),name='amendment_request_reason_choices'),
    re_path(r'^api/search_keywords',proposal_api.SearchKeywordsView.as_view(),name='search_keywords'),
    re_path(r'^api/search_reference',proposal_api.SearchReferenceView.as_view(),name='search_reference'),
    re_path(r'^api/oracle_job$',main_api.OracleJob.as_view(), name='get-oracle'),
    re_path(r'^api/reports/booking_settlements$', main_api.BookingSettlementReportView.as_view(),name='booking-settlements-report'),
    re_path(r'^api/external_dashboard_sections_list/$',main_api.GetExternalDashboardSectionsList.as_view(), name='get-external-dashboard-sections-list'),
    
]

# URL Patterns
urlpatterns = [
    # re_path(r'^ledger/admin/', admin.site.urls, name='ledger_admin'),
    path(r"admin/", admin.site.urls),
    re_path(r'^chaining/', include('smart_selects.urls')),
    re_path(r'', include(api_patterns)),
    # re_path(r'^$', views.MooringLicensingRoutingView.as_view(), name='ds_home'),
    re_path(r'^$', views.MooringLicensingRoutingView.as_view(), name='home'),
    re_path(r'^contact/', views.MooringLicensingContactView.as_view(), name='ds_contact'),
    re_path(r'^further_info/', views.MooringLicensingFurtherInformationView.as_view(), name='ds_further_info'),
    re_path(r'^internal/', views.InternalView.as_view(), name='internal'),
    re_path(r'^external/', views.ExternalView.as_view(), name='external'),
    re_path(r'^firsttime/$', views.first_time, name='first_time'),
    re_path(r'^account/$', views.ExternalView.as_view(), name='manage-account'),
    re_path(r'^profiles/', views.ExternalView.as_view(), name='manage-profiles'),
    re_path(r'^help/(?P<application_type>[^/]+)/(?P<help_type>[^/]+)/$', views.HelpView.as_view(), name='help'),
    re_path(r'^mgt-commands/$', views.ManagementCommandsView.as_view(), name='mgt-commands'),
    re_path(r'^login-success/$', views.LoginSuccess.as_view(), name='login-success'),

    #following url is used to include url path when sending Proposal amendment request to user.
    re_path(r'^proposal/$', proposal_views.ProposalView.as_view(), name='proposal'),
    re_path(r'^preview/licence-pdf/(?P<proposal_pk>\d+)',proposal_views.PreviewLicencePDFView.as_view(), name='preview_licence_pdf'),

    # payment related urls
    re_path(r'^application_fee/(?P<proposal_pk>\d+)/$', ApplicationFeeView.as_view(), name='application_fee'),
    re_path(r'^application_fee_existing/(?P<invoice_reference>\d+)/$', ApplicationFeeExistingView.as_view(), name='application_fee_existing'),
    re_path(r'^application_fee_already_paid/(?P<proposal_pk>\d+)/$', ApplicationFeeAlreadyPaid.as_view(), name='application_fee_already_paid'),
    # re_path(r'^application_fee_already_paid/$', ApplicationFeeAlreadyPaid.as_view(), name='application_fee_already_paid'),
    re_path(r'^confirmation/(?P<proposal_pk>\d+)/$', ConfirmationView.as_view(), name='confirmation'),
    re_path(r'^success/fee/(?P<uuid>.+)/$', ApplicationFeeSuccessView.as_view(), name='fee_success'),
    # re_path(r'^success2/fee/$', ApplicationFeeSuccessViewPreload.as_view(), name='fee_success_preload'),
    re_path(r"ledger-api-success-callback/(?P<uuid>.+)/", ApplicationFeeSuccessViewPreload.as_view(), name="ledger-api-success-callback",),
    re_path(r'^dcv_permit_fee/(?P<dcv_permit_pk>\d+)/$', DcvPermitFeeView.as_view(), name='dcv_permit_fee'),
    re_path(r'^dcv_permit_success/(?P<uuid>.+)/$', DcvPermitFeeSuccessView.as_view(), name='dcv_permit_fee_success'),
    re_path(r'^dcv_permit_success_preload/(?P<uuid>.+)/$', DcvPermitFeeSuccessViewPreload.as_view(), name='dcv_permit_fee_success_preload'),
    re_path(r'^dcv_admission_fee/(?P<dcv_admission_pk>\d+)/$', DcvAdmissionFeeView.as_view(), name='dcv_admission_fee'),
    re_path(r'^dcv_admission_success/(?P<uuid>.+)/$', DcvAdmissionFeeSuccessView.as_view(), name='dcv_admission_fee_success'),
    re_path(r'^dcv_admission_success_preload/(?P<uuid>.+)/$', DcvAdmissionFeeSuccessViewPreload.as_view(), name='dcv_admission_fee_success_preload'),
    re_path(r'^sticker_replacement_fee/$', StickerReplacementFeeView.as_view(), name='sticker_replacement_fee'),
    re_path(r'^sticker_replacement_fee_success/(?P<uuid>.+)/$', StickerReplacementFeeSuccessView.as_view(), name='sticker_replacement_fee_success'),
    re_path(r'^sticker_replacement_fee_success_preload/(?P<uuid>.+)/$', StickerReplacementFeeSuccessViewPreload.as_view(), name='sticker_replacement_fee_success_preload'),
    re_path(r'^aua_for_endorsement/(?P<uuid_str>[a-zA-Z0-9-]+)/view/$', AuthorisedUserApplicationEndorseView.as_view(), {'action': 'view'}, name='view-url'),
    re_path(r'^aua_for_endorsement/(?P<uuid_str>[a-zA-Z0-9-]+)/endorse/$', AuthorisedUserApplicationEndorseView.as_view(), {'action': 'endorse'}, name='endorse-url'),
    re_path(r'^aua_for_endorsement/(?P<uuid_str>[a-zA-Z0-9-]+)/decline/$', AuthorisedUserApplicationEndorseView.as_view(), {'action': 'decline'}, name='decline-url'),
    re_path(r'^mla_documents_upload/(?P<uuid_str>[a-zA-Z0-9-]+)/$', MooringLicenceApplicationDocumentsUploadView.as_view(), name='mla-documents-upload'),
    re_path(r'^dcv_admission_form/$', DcvAdmissionFormView.as_view(), name='dcv_admission_form'),
    re_path(r'payments/invoice-pdf/(?P<reference>\d+)', InvoicePDFView.as_view(), name='invoice-pdf'),
    re_path(r'payments/dcv-permit-pdf/(?P<id>\d+)', DcvPermitPDFView.as_view(), name='dcv-permit-pdf'),
    re_path(r'payments/dcv-admission-pdf/(?P<id>\d+)', DcvAdmissionPDFView.as_view(), name='dcv-admission-pdf'),

    #following url is defined so that to include url path when sending Proposal amendment request to user.
    re_path(r'^external/proposal/(?P<proposal_pk>\d+)/$', views.ExternalProposalView.as_view(), name='external-proposal-detail'),
    re_path(r'^internal/proposal/(?P<proposal_pk>\d+)/$', views.InternalProposalView.as_view(), name='internal-proposal-detail'),
    re_path(r'^external/compliance/(?P<compliance_pk>\d+)/$', views.ExternalComplianceView.as_view(), name='external-compliance-detail'),
    re_path(r'^internal/compliance/(?P<compliance_pk>\d+)/$', views.InternalComplianceView.as_view(), name='internal-compliance-detail'),

    # reversion history-compare
    re_path(r'^history/proposal/(?P<pk>\d+)/$', proposal_views.ProposalHistoryCompareView.as_view(), name='proposal_history'),
    re_path(r'^history/filtered/(?P<pk>\d+)/$', proposal_views.ProposalFilteredHistoryCompareView.as_view(), name='proposal_filtered_history'),
    re_path(r'^history/approval/(?P<pk>\d+)/$', proposal_views.ApprovalHistoryCompareView.as_view(), name='approval_history'),
    re_path(r'^history/compliance/(?P<pk>\d+)/$', proposal_views.ComplianceHistoryCompareView.as_view(), name='compliance_history'),
    re_path(r'^history/helppage/(?P<pk>\d+)/$', proposal_views.HelpPageHistoryCompareView.as_view(), name='helppage_history'),
    re_path(r'^history/organisation/(?P<pk>\d+)/$', organisation_views.OrganisationHistoryCompareView.as_view(), name='organisation_history'),

    re_path(r'^proposal-payment-history/(?P<pk>[0-9]+)/', ProposalPaymentHistoryView.as_view(), name='view_proposal_payment_history'),
    re_path(r'^proposal-payment-history-refund/(?P<pk>[0-9]+)/', RefundProposalHistoryView.as_view(), name='view_refund_proposal_payment_history'),
    re_path(r'^api/check_oracle_code$', payments_api.CheckOracleCodeView.as_view(), name='check_oracle_code'),
    re_path(r'^api/refund_oracle$', payments_api.RefundOracleView.as_view(), name='refund_oracle'),

    re_path(r'^private-media/', views.getPrivateFile, name='view_private_file'),
    re_path(r'^api/remove-AUP-from-mooring/(?P<mooring_id>\d+)/(?P<approval_id>\d+)$',approval_api.removeAUPFromMooring, name='remove_AUP_from_mooring'),
   re_path(r'^api/remove-mooring-from-approval/(?P<mooring_name>[\w-]+)/(?P<approval_id>\d+)/$',approval_api.removeMooringFromApproval, name='remove_mooring_from_approval'),
] + ledger_patterns #+ media_serv_patterns



if settings.DEBUG:  # Serve media locally in development.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.SHOW_DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns = [
        re_path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

if not are_migrations_running():
    DefaultDataManager()

admin.site.site_header = "RIA Mooring Licensing System Administration"
admin.site.site_title = "RIA Mooring Licensing Site"
admin.site.index_title = "RIA Mooring Licensing"

