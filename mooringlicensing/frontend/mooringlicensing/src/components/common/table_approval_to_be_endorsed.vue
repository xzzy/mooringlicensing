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
import { api_endpoints, helpers } from '@/utils/hooks'
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
                dom: 'lBfrtip',
                buttons:[
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
                        // 3. Mooring
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return 'not implemented'
                        }
                    },
                    {
                        // 4. Applicant
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return 'not implemented'
                        }
                    },
                    {
                        // 5. Status
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return 'not implemented'
                        }
                    },
                    {
                        // 10. Action
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return 'View<br />Revoke<br />Process'
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
            return this.level == 'external'
        },

    },
    methods: {

    },
    created: function(){

    },
    mounted: function(){

    }
}
</script>
