<template>
    <div>
        <div class="row">
            <div class="col-lg-12">
                <input type="checkbox"> Show expired and/or surrendered waiting list allocations
            </div>
        </div>

        <div class="row">
            <div class="col-lg-12">
                <datatable 
                    ref="waiting_list_datatable" 
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
import { api_endpoints, helpers }from '@/utils/hooks'
export default {
    name: 'TableWaitingList',
    data() {
        let vm = this;
        return {
            datatable_id: 'waiting_lists-datatable-' + vm._uid,
            approvalTypesToDisplay: ['wla'],

            // Datatable settings
            datatable_headers: ['Id', 'Number', 'Bay', 'number', 'Status', 'Vessel Registration', 'Vessel Name', 'Issue Date', 'Expiry Date', 'Action'],
            //datatable_headers: ['Id', 'Number', 'Bay', 'Application number in Bay', 'Status', 'Vessel Registration', 'Vessel Name', 'Issue Date', 'Expiry Date', 'Action'],
            datatable_options: {
                autoWidth: false,
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                serverSide: true,
                searching: false,
                ajax: {
                    "url": api_endpoints.approvals_paginated_external + '?format=datatables',
                    "dataSrc": 'data',

                    // adding extra GET params for Custom filtering
                    "data": function ( d ) {
                        d.filter_approval_types = vm.approvalTypesToDisplay.join(',');
                    }
                },
                dom: 'frt', //'lBfrtip',
                buttons:[
                    //{
                    //    extend: 'excel',
                    //    exportOptions: {
                    //        columns: ':visible'
                    //    }
                    //},
                    //{
                    //    extend: 'csv',
                    //    exportOptions: {
                    //        columns: ':visible'
                    //    }
                    //},
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
                        // 3. Bay
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return 'not implemented'
                        }
                    },
                    {
                        // 4. Application number in Bay
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
                            return full.status
                        }
                    },
                    {
                        // 6. Vessel Registration
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return 'not implemented'
                        }
                    },
                    {
                        // 7. Vessel Name
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return 'not implemented'
                        }
                    },
                    {
                        // 8. Issue Date
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return 'not implemented'
                        }
                    },
                    {
                        // 9. Expiry Date
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
                            return 'not implemented'
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

    },
    methods: {

    },
    created: function(){

    },
    mounted: function(){

    }
}
</script>
