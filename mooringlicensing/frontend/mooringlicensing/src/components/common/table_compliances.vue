<template>
    <div>
        <div class="row">
            <div class="col-md-3">
                <div class="form-group">
                    <label for="">Status</label>
                    <select class="form-control" v-model="filterComplianceStatus">
                        <option value="All">All</option>
                        <option v-for="status in compliance_statuses" :value="status.code">{{ status.description }}</option>
                    </select>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-lg-12">
                <datatable 
                    ref="compliances_datatable" 
                    :id="datatable_id" 
                    :dtOptions="compliances_options" 
                    :dtHeaders="compliances_headers"
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
    name: 'TableCompliances',
    data() {
        let vm = this;
        return {
            datatable_id: 'compliances-datatable-' + vm._uid,

            // selected values for filtering
            filterComplianceStatus: null,
            compliance_statuses: [],

            // Datatable settings
            compliances_headers: ['Id', 'Number', 'Licence/Permit', 'Condition', 'Due Date', 'Status', 'Action'],
            compliances_options: {
                searching: false,
                autoWidth: false,
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                serverSide: true,

                ajax: {
                    "url": api_endpoints.compliances_paginated_external + '?format=datatables',
                    "dataSrc": 'data',

                    // adding extra GET params for Custom filtering
                    "data": function ( d ) {
                        // Add filters selected
                        d.filter_compliance_status = vm.filterComplianceStatus;
                    }
                },
                dom: 'lBfrtip',
                buttons:[
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
                        // 3. Licence/Permit
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return 'not implemented'
                        }
                    },
                    {
                        // 4. Condition
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return 'not implemented'
                        }
                    },
                    {
                        // 5. Due Date
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return 'not implemented'
                        }
                    },
                    {
                        // 6. Status
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.status
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
        fetchFilterLists: function(){
            let vm = this;

            // Statuses
            vm.$http.get(api_endpoints.compliance_statuses_dict).then((response) => {
                vm.compliance_statuses = response.body
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
