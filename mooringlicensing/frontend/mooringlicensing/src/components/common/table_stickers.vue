<template>
    <div>
        <div class="row">
            <div class="col-md-3">
                <div class="form-group">
                    <label for="">Permit or licence type</label>
                    <select class="form-control" v-model="filterApprovalType">
                        <option value="All">All</option>
                        <option v-for="type in approval_types" :value="type.code">{{ type.description }}</option>
                    </select>
                </div>
            </div>
            <div class="col-md-3">
                <div class="form-group">
                    <label for="">Year</label>
                    <select class="form-control" v-model="filterYear">
                        <option value="All">All</option>

                    </select>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-12">
                <button type="button" class="btn btn-primary pull-right" @click="export_to_csv_button_clicked">Export to CSV</button>
            </div>
        </div>

        <div class="row">
            <div class="col-lg-12">
                <datatable
                    ref="stickers_datatable"
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
            datatable_id: 'applications-datatable-' + vm._uid,
            approvalTypesToDisplay: ['aap', 'aup', 'ml'],

            // selected values for filtering
            filterApprovalType: null,
            filterYear: null,

            // filtering options
            approval_types: [],
            debug: false,
        }
    },
    components:{
        datatable
    },
    watch: {
        filterYear: function() {
            let vm = this;
            vm.$refs.stickers_datatable.vmDataTable.draw();  // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
            //if (vm.filterApplicationStatus != 'All') {
            //    vm.$refs.stickers_datatable.vmDataTable.column('status:name').search('').draw();
            //} else {
            //    vm.$refs.stickers_datatable.vmDataTable.column('status:name').search(vm.filterApplicationStatus).draw();
            //}
        },
        filterApprovalType: function() {
            let vm = this;
            vm.$refs.stickers_datatable.vmDataTable.draw();  // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
        },
    },
    computed: {
        is_external: function() {
            return this.level == 'external'
        },
        is_internal: function() {
            return this.level == 'internal'
        },
        datatable_headers: function(){
            if (this.is_external){
                return []
            }
            if (this.is_internal){
                return ['id', 'Number', 'Permit or Licence', 'Date sent / printed / mailed', 'Status', 'Year', 'Action']
            }
        },
        column_id: function(){
            return {
                // 1. ID
                data: "id",
                orderable: false,
                searchable: false,
                visible: false,
                'render': function(row, type, full){
                    return full.id
                }
            }
        },
        column_number: function(){
            return {
                // 2. Number
                data: "number",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function(row, type, full){
                    return full.number
                },
                name: 'number',
            }
        },
        column_permit_or_licence: function(){
            return {
                data: "approval",
                orderable: true,
                searchable: false,
                visible: true,
                'render': function(row, type, full){
                    return '<a href="/internal/approval/' + full.approval.id + '">' + full.approval.lodgement_number + '</a>'
                }
            }
        },
        column_printing_company: function(){
            return {
                // 4. Application Type (This corresponds to the 'ProposalType' at the backend)
                data: "id",
                orderable: true,
                searchable: false,
                visible: true,
                'render': function(row, type, full){
                    return full.sent_date + '<br />' + full.printing_date + '<br />' + full.mailing_date
                }
            }
        },
        column_status: function(){
            let vm = this
            return {
                // 5. Status
                data: "status",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function(row, type, full){
                    return '<span id="status_cell_id_' + full.id + '">' + full.status + '</span>'
                },
                name: 'status'
            }
        },
        column_year: function(){
            return {
                // 6. Lodged
                data: "id",
                orderable: true,
                searchable: false,
                visible: true,
                'render': function(row, type, full){
                    return 'not implemented'
                }
            }
        },
        column_action: function(){
            let vm = this
            return {
                // 8. Action
                data: "id",
                orderable: true,
                searchable: false,
                visible: true,
                'render': function(row, type, full){
                    let links =  `<a href='#${full.id}' data-replacement='${full.id}'>Request Sticker Replacement</a><br/>`
                    links += `<a href='#${full.id}' data-record-returned='${full.id}'>Record Returned Sticker</a><br/>`
                    links += `<a href='#${full.id}' data-record-lost='${full.id}'>Record Sticker Lost</a><br/>`

                    return links
                }
            }
        },
        datatable_options: function(){
            let vm = this

            let columns = []
            let search = null
            if(vm.is_external){
                columns = []
                search = false
            }
            if(vm.is_internal){
                columns = [
                    vm.column_id,
                    vm.column_number,
                    vm.column_permit_or_licence,
                    vm.column_printing_company,
                    vm.column_status,
                    vm.column_year,
                    vm.column_action,
                ]
                search = true
            }

            return {
                autoWidth: false,
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                serverSide: true,
                searching: search,
                ordering: true,
                order: [[1, 'desc']],  // Default order [[column_index, 'asc/desc'], ...]
                ajax: {
                    "url": api_endpoints.stickers_paginated_list + '?format=datatables&debug=' + vm.debug,
                    "dataSrc": 'data',

                    // adding extra GET params for Custom filtering
                    "data": function ( d ) {
                        d.filter_approval_type = vm.filterApprovalType
                        d.filter_year = vm.filterYear
                        d.level = vm.level
                    }
                },
                dom: 'lBfrtip',
                buttons:[ ],
                columns: columns,
                processing: true,
                initComplete: function() {
                    console.log('in initComplete')
                },
            }
        }
    },
    methods: {
        export_to_csv_button_clicked: function(){
            console.log('Export to CSV button clicked')
        },
        //discardProposal: function(proposal_id) {
        //    let vm = this;
        //    swal({
        //        title: "Discard Application",
        //        text: "Are you sure you want to discard this proposal?",
        //        type: "warning",
        //        showCancelButton: true,
        //        confirmButtonText: 'Discard Application',
        //        confirmButtonColor:'#dc3545'
        //    }).then(() => {
        //        vm.$http.delete(api_endpoints.discard_proposal(proposal_id))
        //        .then((response) => {
        //            console.log('response: ')
        //            console.log(response)
        //            swal(
        //                'Discarded',
        //                'Your proposal has been discarded',
        //                'success'
        //            )
        //            //vm.$refs.stickers_datatable.vmDataTable.ajax.reload();
        //            vm.$refs.stickers_datatable.vmDataTable.draw();
        //        }, (error) => {
        //            console.log(error);
        //        });
        //    },(error) => {

        //    });
        //},
        fetchFilterLists: function(){
            let vm = this;

            let include_codes = vm.approvalTypesToDisplay.join(',');
            //vm.$http.get(api_endpoints.approval_types_dict + '?include_codes=' + include_codes).then((response) => {

            // Application Types
            vm.$http.get(api_endpoints.approval_types_dict+'?include_codes=' + include_codes).then((response) => {
                vm.approval_types = response.body
            },(error) => {
                console.log(error);
            })

            // TODO: Fetch Years
        },
        updateStatusCell: function(id, newText){
            let elem = $('#status_cell_id_' + id)
            elem.fadeOut(function(){
                elem.text(newText).fadeIn()
            })
        },
        addEventListeners: function(){
            let vm = this

            vm.$refs.stickers_datatable.vmDataTable.on('click', 'a[data-replacement]', function(e) {
                e.preventDefault();
                let id = $(this).attr('data-replacement');
                vm.$emit("actionClicked", {"action": "request_replacement", "id": id})
            });
            vm.$refs.stickers_datatable.vmDataTable.on('click', 'a[data-record-returned]', function(e) {
                e.preventDefault();
                let id = $(this).attr('data-record-returned');
                vm.$emit("actionClicked", {"action": "record_returned", "id": id})
            });
            vm.$refs.stickers_datatable.vmDataTable.on('click', 'a[data-record-lost]', function(e) {
                e.preventDefault();
                let id = $(this).attr('data-record-lost');
                vm.$emit("actionClicked", {"action": "record_lost", "id": id})
            });
        },
    },
    created: function(){
        this.fetchFilterLists()
        if (this.$route.query && this.$route.query.debug){
            this.debug = this.$route.query.debug
        }
    },
    mounted: function(){
        let vm = this;
        this.$nextTick(() => {
            vm.addEventListeners();
        });
    }
}
</script>
