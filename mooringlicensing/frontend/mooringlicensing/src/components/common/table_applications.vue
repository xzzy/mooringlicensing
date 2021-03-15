<template>
    <div>
        <div class="row">
            <div class="col-md-3">
                <div class="form-group">
                    <label for="">Type</label>
                    <select class="form-control" v-model="filterApplicationType">
                        <option value="All">All</option>
                        <option v-for="type in application_types" :value="type.code">{{ type.description }}</option>
                    </select>
                </div>
            </div>
            <div class="col-md-3">
                <div class="form-group">
                    <label for="">Status</label>
                    <select class="form-control" v-model="filterApplicationStatus">
                        <option value="All">All</option>
                        <option v-for="status in application_statuses" :value="status.code">{{ status.description }}</option>
                    </select>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-12">
                <button type="button" class="btn btn-primary pull-right" @click="new_application_button_clicked">New Application</button>
            </div>
        </div>

        <div class="row">
            <div class="col-lg-12">
                <datatable 
                    ref="application_datatable" 
                    :id="datatable_id" 
                    :dtOptions="datatable_options" 
                    :dtHeaders="datatable_headers"
                />
            </div>
        </div>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue'
import Vue from 'vue'
import { api_endpoints, helpers } from '@/utils/hooks'
export default {
    name: 'TableApplications',
    data() {
        let vm = this;
        return {
            datatable_id: 'applications-datatable-' + vm._uid,

            // selected values for filtering
            filterApplicationType: null,
            filterApplicationStatus: null,

            // filtering options
            application_types: ['test1', 'test2'],
            application_statuses: ['test3', 'test4'],

            // Datatable settings
            datatable_headers: ['id', 'Number', 'Type', 'Application Type', 'Status', 'Lodged', 'Action'],
            datatable_options: {
                autoWidth: false,
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                serverSide: true,
                searching: true,
                ajax: {
                    "url": api_endpoints.proposals_paginated_external + '?format=datatables',
                    "dataSrc": 'data',

                    // adding extra GET params for Custom filtering
                    "data": function ( d ) {
                        d.filter_application_type = vm.filterApplicationType;
                        d.filter_application_status = vm.filterApplicationStatus;
                    }
                },
                dom: 'lBfrtip',
                buttons:[
                    {
                        extend: 'excel',
                        exportOptions: {
                            columns: ':visible'
                        }
                    },
                    {
                        extend: 'csv',
                        exportOptions: {
                            columns: ':visible'
                        }
                    },
                ],
                columns: [
                    {
                        // 1. ID
                        data: "id",
                        orderable: false,
                        searchable: false,
                        visible: false,
                        'render': function(row, type, full){
                            return full.id
                        }
                    },
                    {
                        // 2. Lodgement Number
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.lodgement_number
                        }
                    },
                    {
                        // 3. Type (This corresponds to the 'ApplicationType' at the backend)
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.application_type_dict.description
                        }
                    },
                    {
                        // 4. Application Type (This corresponds to the 'ProposalType' at the backend)
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.proposal_type
                        }
                    },
                    {
                        // 5. Status
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.customer_status
                        }
                    },
                    {
                        // 6. Lodged
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.lodgement_date
                        }
                    },
                    {
                        // 7. Action
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return 'not implemented'
                        }
                    },
                    //{
                    //    // 4. Submitter
                    //    data: "submitter",
                    //    mRender:function (data,type,full) {
                    //        if (data) {
                    //            return `${data.first_name} ${data.last_name}`;
                    //        }
                    //        return ''
                    //    },
                    //    //name: vm.submitter_column_name,
                    //    name: "submitter__email, submitter__first_name, submitter__last_name",
                    //    searchable: true,
                    //},
                    //{
                    //    // 5. Proponent/Applicant
                    //    data: "relevant_applicant_name",
                    //    //name: vm.proponent_applicant_column_name,
                    //    name: "applicant__organisation__name, proxy_applicant__first_name, proxy_applicant__last_name, proxy_applicant__email",
                    //    searchable: true,
                    //},
                    //{
                    //    // 6. Status
                    //    mRender:function (data, type, full) {
                    //        if (vm.is_external){
                    //            return full.customer_status
                    //        }
                    //        return full.processing_status
                    //    },
                    //    searchable: false,
                    //    name: 'status',
                    //},
                    //{
                    //    // 7. Lodged on
                    //    data: "lodgement_date",
                    //    mRender:function (data,type,full) {
                    //        return data != '' && data != null ? moment(data).format(vm.dateFormat): '';
                    //    },
                    //    searchable: true,
                    //},
                    //{
                    //    // 8. Assigned Officer
                    //    data: "assigned_officer",
                    //    visible: false,
                    //    name: "assigned_officer__first_name, assigned_officer__last_name, assigned_officer__email",
                    //    searchable: true,
                    //},
                    //{
                    //    // 9. Invoice
                    //    mRender:function (data, type, full) {
                    //        console.log(full)
                    //        let links = '';
                    //        //if (full.fee_paid) {
                    //        //    links +=  `<a href='/payments/invoice-pdf/${full.fee_invoice_reference}.pdf' target='_blank'><i style='color:red;' class='fa fa-file-pdf-o'></i></a> &nbsp`;
                    //        //    if (!vm.is_external){
                    //        //        links +=  `<a href='/ledger/payments/invoice/payment?invoice=${full.fee_invoice_reference}' target='_blank'>View Payment</a><br/>`;
                    //        //    }
                    //        //}
                    //        if (full.fee_invoice_references){
                    //            for (let item of full.fee_invoice_references){
                    //                links += '<div>'
                    //                links +=  `<a href='/payments/invoice-pdf/${item}.pdf' target='_blank'><i style='color:red;' class='fa fa-file-pdf-o'></i> #${item}</a>`;
                    //                if (!vm.is_external){
                    //                    links +=  `&nbsp;&nbsp;&nbsp;<a href='/ledger/payments/invoice/payment?invoice=${item}' target='_blank'>View Payment</a><br/>`;
                    //                }
                    //                links += '</div>'
                    //            }
                    //        }
                    //        return links;
                    //    },
                    //    name: 'invoice_column',
                    //    orderable: false,
                    //    visible: false,
                    //    searchable: false,
                    //},
                    //{
                    //    // 10. Action
                    //    mRender:function (data,type,full) {
                    //        let links = '';
                    //        if (!vm.is_external){
                    //            if(full.assessor_process){
                    //                links +=  `<a href='/internal/proposal/${full.id}'>Process</a><br/>`;
                    //            } else {
                    //                links +=  `<a href='/internal/proposal/${full.id}'>View</a><br/>`;
                    //            }
                    //        }
                    //        else{
                    //            if (full.can_user_edit) {
                    //                links +=  `<a href='/external/proposal/${full.id}'>Continue</a><br/>`;
                    //                links +=  `<a href='#${full.id}' data-discard-proposal='${full.id}'>Discard</a><br/>`;
                    //            }
                    //            else if (full.can_user_view) {
                    //                links +=  `<a href='/external/proposal/${full.id}'>View</a><br/>`;
                    //            }
                    //        }
                    //        return links;
                    //    },
                    //    name: '',
                    //    searchable: false,
                    //    orderable: false
                    //},
                ],
                processing: true,
                initComplete: function() {
                    console.log('in initComplete')
                },
            },
        }
    },
    components:{
        datatable
    },
    watch: {
        filterApplicationStatus: function() {
            let vm = this;
            vm.$refs.application_datatable.vmDataTable.draw();  // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
            //if (vm.filterApplicationStatus != 'All') {
            //    vm.$refs.application_datatable.vmDataTable.column('status:name').search('').draw();
            //} else {
            //    vm.$refs.application_datatable.vmDataTable.column('status:name').search(vm.filterApplicationStatus).draw();
            //}
        },
        filterApplicationType: function() {
            let vm = this;
            vm.$refs.application_datatable.vmDataTable.draw();  // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
            //if (vm.filterApplicationType != 'All') {
            //    vm.$refs.application_datatable.vmDataTable.column('status:name').search('').draw();
            //} else {
            //    vm.$refs.application_datatable.vmDataTable.column('status:name').search(vm.filterApplicationType).draw();
            //}
        },

    },
    computed: {

    },
    methods: {
        new_application_button_clicked: function(){
            this.$router.push({
                name: 'apply_proposal'
            })
        },
        fetchFilterLists: function(){
            let vm = this;

            // Application Types
            vm.$http.get(api_endpoints.application_types_dict+'?apply_page=False').then((response) => {
                vm.application_types = response.body
            },(error) => {
                console.log(error);
            })

            // Application Statuses
            vm.$http.get(api_endpoints.application_statuses_dict).then((response) => {
                vm.application_statuses = response.body
            },(error) => {
                console.log(error);
            })
        },
    },
    created: function(){
        this.fetchFilterLists()
    },
    mounted: function(){

    }
}
</script>
