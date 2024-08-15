<template>
    <div>
        <div class="row">

        </div>

        <div class="row">
            <div class="col-lg-12">
                <datatable 
                    ref="to_be_endorsed_datatable" 
                    :id="datatable_id" 
                    :dtOptions="to_be_endorsed_options" 
                    :dtHeaders="to_be_endorsed_headers"
                />
            </div>
        </div>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue'
import Vue from 'vue'
import { api_endpoints, helpers, constants } from '@/utils/hooks'
export default {
    name: 'TableCompliances',
    props: {
        level:{
            type: String,
            required: true,
            validator: function(val) {
                let options = ['internal', 'referral', 'external'];
                return options.indexOf(val) != -1 ? true: false;
            }
        },
    },
    data() {
        let vm = this;
        let buttons = []
        if (vm.is_internal){
            buttons = [
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
            ]
        }

        return {
            datatable_id: 'to_be_endorsed-datatable-' + vm._uid,
            approvalTypesToDisplay: ['aua'],

            // selected values for filtering
            filterApplicationType: null,
            filterApplicationStatus: null,
            filter_by_endorsement: true,

            // Datatable settings
            to_be_endorsed_headers: ['Id', 'Number', 'Mooring', 'Applicant', 'Status', 'Action'],
            to_be_endorsed_options: {
                autoWidth: false,
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                serverSide: true,
                searching: false,
                ajax: {
                    "url": api_endpoints.proposals_paginated_list + '?format=datatables',
                    "dataSrc": 'data',

                    // adding extra GET params for Custom filtering
                    "data": function ( d ) {
                        d.filter_approval_type = vm.approvalTypesToDisplay.join(',')

                        // Add filters selected
                        //d.filter_approval_type = vm.filterApprovalType
                        d.filter_approval_status = vm.filterApprovalStatus
                        d.filter_by_endorsement = vm.filter_by_endorsement
                    }
                },
                // dom: 'lBfrtip',
                dom: 'lBfrtp',
                buttons: buttons,
                columns: [
                    {
                        // 1. ID
                        data: "id",
                        orderable: false,
                        searchable: false,
                        visible: false,
                        'render': function(row, type, full){
                            console.log(full)
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
                        // 3. Mooring
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            if (full.mooring){
                                return full.mooring.name
                            }
                            return ''
                        }
                    },
                    {
                        // 4. Applicant
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.applicant.legal_first_name + ' ' + full.applicant.legal_last_name
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
                        // 10. Action
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            //return 'View<br />Endorse<br />Decline'
                            let links = '';
                            // links +=  `<a href='/aua_for_endorsement/${full.uuid}/view/'>View</a><br/>`;
                            links +=  `<a href='/external/proposal/${full.uuid}/'>View</a><br/>`;
                            if(full.customer_status === constants.AWAITING_ENDORSEMENT){
                                // links +=  `<a href='/aua_for_endorsement/${full.uuid}/endorse/'>Endorse</a><br/>`;
                                // links +=  `<a href='/aua_for_endorsement/${full.uuid}/decline/'>Decline</a><br/>`;
                                // links +=  `<a href='#${full.id}' data-request-new-sticker='${full.id}'>Request New Sticker</a><br/>`
                                links +=  `<a href='#${full.id}' data-approve-endorsement='${full.uuid}'>Endorse</a><br/>`
                                links +=  `<a href='#${full.id}' data-decline-endorsement='${full.uuid}'>Decline</a><br/>`
                                // links +=  `<a href='/aua_for_endorsement/${full.uuid}/decline/'>Decline</a><br/>`;
                            }
                            return links
                        }
                    },
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

    },
    computed: {
        is_external: function() {
            return this.level === 'external'
        },
        is_internal: function() {
            return this.level === 'internal'
        },
    },
    methods: {
        addEventListeners: function(){
            let vm = this
            vm.$refs.to_be_endorsed_datatable.vmDataTable.on('click', 'a[data-approve-endorsement]', function(e) {
                e.preventDefault();
                var uuid = $(this).attr('data-approve-endorsement');
                vm.approveEndorsement(uuid);
            })
            vm.$refs.to_be_endorsed_datatable.vmDataTable.on('click', 'a[data-decline-endorsement]', function(e) {
                e.preventDefault();
                var uuid = $(this).attr('data-decline-endorsement');
                vm.declineEndorsement(uuid);
            })
        },
        approveEndorsement: function(uuid){
            let vm = this
            swal({
                title: "Endorse Application",
                text: "Are you sure you want to endorse this application?",
                type: "warning",
                showCancelButton: true,
                confirmButtonText: 'Endorse Application',
                confirmButtonColor:'#dc3545'
            }).then(() => {
                vm.$http.get('/aua_for_endorsement/' + uuid + '/endorse/')
                .then((response) => {
                    swal(
                        'Endorsed',
                        'Application has been endorsed',
                        'success'
                    )
                    vm.$refs.to_be_endorsed_datatable.vmDataTable.draw();
                }, (error) => {

                });
            },(error) => {

            });
        },
        declineEndorsement: function(uuid){
            let vm = this
            swal({
                title: "Decline approval",
                text: "Are you sure you want to decline approval?",
                type: "warning",
                showCancelButton: true,
                confirmButtonText: 'Decline Approval',
                confirmButtonColor:'#dc3545'
            }).then(() => {
                vm.$http.get('/aua_for_endorsement/' + uuid + '/decline/')
                .then((response) => {
                    swal(
                        'Declined',
                        'Application has been declined',
                        'success'
                    )
                    vm.$refs.to_be_endorsed_datatable.vmDataTable.draw();
                }, (error) => {

                });
            },(error) => {

            });

        },
    },
    created: function(){

    },
    mounted: function(){
        this.$nextTick(() => {
            this.addEventListeners();
        })
    }
}
</script>
