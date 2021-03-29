
module.exports = {
    application_types:"/api/application_types",
    application_types_dict:"/api/application_types_dict",
    application_statuses_dict:"/api/application_statuses_dict",
    vessel_types_dict:"/api/vessel_types_dict",
    vessel_rego_nos:"/api/vessel_rego_nos",
    approval_types_dict:"/api/approval_types_dict",
    approval_statuses_dict:"/api/approval_statuses_dict",
    compliance_statuses_dict:"/api/compliance_statuses_dict",

    profile: '/api/profile',
    organisations: '/api/organisations.json',
    filtered_organisations: '/api/filtered_organisations',
    organisation_requests: '/api/organisation_requests.json',
    organisation_contacts: '/api/organisation_contacts.json',
    organisation_access_group_members: '/api/organisation_access_group_members',
    users: '/api/users.json',
    department_users: '/api/department_users',
    filtered_users: '/api/filtered_users',
    countries: "https://restcountries.eu/rest/v1/?fullText=true",

    proposals_paginated_external: '/api/proposals_paginated/list_external',
    approvals_paginated_external: '/api/approvals_paginated/list_external',
    compliances_paginated_external: '/api/compliances_paginated/list_external',
    waitinglistapplication: '/api/waitinglistapplication/',
    annualadmissionapplication: '/api/annualadmissionapplication/',

    discard_proposal: function (id) {
        return `/api/proposal/${id}.json`;
    },
    /*
    proposals_paginated_internal:   "/api/proposal_paginated/proposals_internal/?format=datatables",
    mooringlicensings: '/api/mooringlicensings/',
    participants: '/api/participants/participants_list',
    parks: '/api/parks/parks_list',
    campgrounds: '/api/campgrounds/campgrounds_list',
    camping_choices: '/api/mooringlicensings/camping_choices',
    filter_list: '/api/mooringlicensings/filter_list/',
    temporary_document: '/api/temporary_document/',
    admin_data: '/admin_data/',
    */
}
