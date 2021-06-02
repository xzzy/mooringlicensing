<template>
    <div>
        <div class="row">
            <div v-if="wlaCheckbox" class="col-lg-12">
                <input type="checkbox" id="checkbox_show_expired" v-model="show_expired_surrendered">
                <label for="checkbox_show_expired">Show expired and/or surrendered waiting list allocations</label>
            </div>
        </div>

        <div class="row">
            <div class="col-lg-12">
                <datatable 
                    ref="approvals_datatable" 
                    :id="datatable_id" 
                    :dtOptions="datatable_options" 
                    :dtHeaders="datatable_headers"
                />
            </div>
        </div>
        <div v-if="wlaCheckbox && selectedWaitingListAllocationId">
            <OfferMooringLicence
                ref="offer_mooring_licence" 
                :key="offerMooringLicenceKey"
                :wlaId="selectedWaitingListAllocationId"
                :mooringBayId="mooringBayId"
                @refreshFromResponse="refreshFromResponse"
            />
        </div>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue'
import OfferMooringLicence from '@/components/internal/approvals/offer_mooring_licence.vue'
import Vue from 'vue'
import { api_endpoints, helpers }from '@/utils/hooks'
export default {
    name: 'TableWaitingList',
    props: {
        approvalTypeFilter: {
            type: Array,
            required: true,
            /*
            validator: function(val) {
                let options = ['wla', 'ml', 'aap', 'aup'];
                return options.indexOf(val) != -1 ? true: false;
            }
            */
        },
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
            datatable_id: 'waiting_lists-datatable-' + vm._uid,
            //approvalTypesToDisplay: ['wla'],
            show_expired_surrendered: true,
            selectedWaitingListAllocationId: null,
            uuid: 0,
            mooringBayId: null,
        }
    },
    components:{
        datatable,
        OfferMooringLicence,
    },
    watch: {
        show_expired_surrendered: function(value){
            console.log(value)
            this.$refs.approvals_datatable.vmDataTable.ajax.reload()
        }
    },
    computed: {
        wlaCheckbox: function() {
            let returnVal = false;
            if (this.approvalTypeFilter.includes('wla')) {
                returnVal = true;
            }
            return returnVal;
        },
        is_external: function() {
            return this.level == 'external'
        },
        is_internal: function() {
            return this.level == 'internal'
        },
        // Datatable settings
        datatable_headers: function() {
            if (this.is_external) {
                return [
                    'Id', 
                    'Number', 
                    'Bay', 
                    'Application number in Bay', 
                    'Status', 
                    'Vessel Registration', 
                    'Vessel Name', 
                    'Issue Date', 
                    'Expiry Date', 
                    'Action'
                ]
            } else if (this.is_internal && this.wlaCheckbox) {
                return [
                    'Id', 
                    'Number', 
                    'Holder',
                    'Status', 
                    'Mooring area',
                    'Allocation number in bay',
                    'Action',
                    'Issue Date', 
                    'Expiry Date', 
                    'Vessel length',
                    'Vessel draft',
                ]
            } else if (this.is_internal) {
                return [
                    'Id', 
                    'Number', 
                    'Holder',
                    'Status', 
                    'Issue Date', 
                    'Expiry Date', 
                    'Vessel length',
                    'Vessel draft',
                    'Mooring area',
                    'Action'
                ]
            }
        },
        columnId: function() {
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
        columnLodgementNumber: function() {
            return {
                        // 2. Lodgement Number
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.lodgement_number
                        }
                    }
        },
        /*
        columnBay: function() {
            return {
                        // 3. Bay
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return 'not implemented'
                        }
                    }
        },
        */
        columnApplicationNumberInBay: function() {
            return {
                        // 4. Application number in Bay
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.current_proposal_number;
                        }
                    }
        },
        columnStatus: function() {
            return {
                        // 5. Status
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.status
                        }
                    }
        },
        columnVesselRegistration: function() {
            return {
                        // 6. Vessel Registration
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.vessel_registration;
                        }
                    }
        },
        columnVesselName: function() {
            return {
                        // 7. Vessel Name
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.vessel_name;
                        }
                    }
        },
        columnIssueDate: function() {
            return {
                        // 8. Issue Date
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.issue_date_str;
                        }
                    }
        },
        columnExpiryDate: function() {
            return {
                        // 9. Expiry Date
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.expiry_date_str;
                        }
                    }
        },
        columnAction: function() {
            let vm = this;
            return {
                        // 10. Action
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.offer_link;
                        }
                    }
        },
        columnHolder: function() {
            return {
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.holder;
                        }
                    }
        },
        columnPreferredMooringBay: function() {
            return {
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.preferred_mooring_bay;
                        }
                    }
        },
        columnAllocationNumberInBay: function() {
            return {
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.wla_order;
                        }
                    }
        },

        columnVesselLength: function() {
            return {
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.vessel_length;
                        }
                    }
        },
        columnVesselDraft: function() {
            return {
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            return full.vessel_draft;
                        }
                    }
        },

        datatable_options: function() {
            let vm = this;
            let selectedColumns = [];
            if (vm.is_external) {
                selectedColumns = [
                    vm.columnId,
                    vm.columnLodgementNumber,
                    //vm.columnBay,
                    vm.columnPreferredMooringBay,
                    vm.columnApplicationNumberInBay,
                    vm.columnStatus,
                    vm.columnVesselRegistration,
                    vm.columnVesselName,
                    vm.columnIssueDate,
                    vm.columnExpiryDate,
                    vm.columnAction,
                ]
            } else if (vm.is_internal && this.wlaCheckbox) {
                selectedColumns = [
                    vm.columnId,
                    vm.columnLodgementNumber,
                    vm.columnHolder,
                    vm.columnStatus,
                    vm.columnPreferredMooringBay,
                    vm.columnAllocationNumberInBay,
                    vm.columnAction,
                    vm.columnIssueDate,
                    vm.columnExpiryDate,
                    vm.columnVesselLength,
                    vm.columnVesselDraft,
                ]
            } else if (vm.is_internal) {
                selectedColumns = [
                    vm.columnId,
                    vm.columnLodgementNumber,
                    vm.columnHolder,
                    vm.columnStatus,
                    vm.columnIssueDate,
                    vm.columnExpiryDate,
                    vm.columnVesselLength,
                    vm.columnVesselDraft,
                    vm.columnPreferredMooringBay,
                    vm.columnAction,
                ]
            }

            return {
                autoWidth: false,
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                serverSide: true,
                //searching: false,
                searching: true,
                ajax: {
                    "url": api_endpoints.approvals_paginated_list + '?format=datatables',
                    "dataSrc": 'data',

                    // adding extra GET params for Custom filtering
                    "data": function ( d ) {
                        //d.filter_approval_type = vm.approvalTypesToDisplay.join(',');
                        d.filter_approval_type = vm.approvalTypeFilter.join(',');
                        d.show_expired_surrendered = vm.show_expired_surrendered
                    }
                },
                //dom: 'frt', //'lBfrtip',
                dom: 'lBfrtip',
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
                columns: selectedColumns,
                processing: true,
                initComplete: function() {
                    console.log('in initComplete')
                },
            }
        },
        offerMooringLicenceKey: function() {
            return 'offer_mooring_licence_' + this.selectedWaitingListAllocationId + '_' + this.uuid;
        },

    },
    methods: {
        offerMooringLicence: function(id){
            console.log('offerMooringLicence')
            console.log(id)
            this.selectedWaitingListAllocationId = parseInt(id);
            this.uuid++;
            this.$nextTick(() => {
                this.$refs.offer_mooring_licence.isModalOpen = true;
            });
        },
        refreshFromResponse: async function(lodgementNumber){
            console.log("refreshFromResponse");
            await swal({
                title: "Saved",
                text: 'Mooring Licence Application ' + lodgementNumber + ' has been created',
                type:'success'
            });
            await this.$refs.approvals_datatable.vmDataTable.ajax.reload();
        },
        addEventListeners: function(){
            let vm = this;
            //Internal Action shortcut listeners
            let table = vm.$refs.approvals_datatable.vmDataTable
            table.on('processing.dt', function(e) {
            })
            table.on('click', 'a[data-offer]', async function(e) {
                e.preventDefault();
                var id = $(this).attr('data-offer');
                vm.mooringBayId = parseInt($(this).attr('data-mooring-bay'));
                await vm.offerMooringLicence(id);
            }).on('responsive-display.dt', function () {
                var tablePopover = $(this).find('[data-toggle="popover"]');
                if (tablePopover.length > 0) {
                    tablePopover.popover();
                    // the next line prevents from scrolling up to the top after clicking on the popover.
                    $(tablePopover).on('click', function (e) {
                        e.preventDefault();
                        return true;   
                    });
                }
            }).on('draw.dt', function () {
                var tablePopover = $(this).find('[data-toggle="popover"]');
                if (tablePopover.length > 0) {
                    tablePopover.popover();
                    // the next line prevents from scrolling up to the top after clicking on the popover.
                    $(tablePopover).on('click', function (e) {
                        e.preventDefault();
                        return true;   
                    });
                }
            });
        },
    },
    created: function(){

    },
    mounted: function(){
        this.$nextTick(() => {
            this.addEventListeners();
        });
    }
}
</script>
