<template lang="html">
    <div id="change-contact">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="title" large>
            <div class="container-fluid">
                <alert :show.sync="showError" type="danger"><strong>{{ errorString }}</strong></alert>
                <div class="row form-group">
                    <!-- <table class="table table-striped table-bordered">
                        <thead>
                            <tr>
                                <th scope="col"></th>
                                <th scope="col">Number</th>
                                <th scope="col">vessel</th>
                                <th scope="col">mooring</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="sticker in stickers" :key="sticker.id">
                                <td><input type="checkbox" v-model="sticker.checked" /></td>
                                <td>{{ sticker.number }}</td>
                                <td>{{ sticker.vessel.rego_no }}</td>
                                <td>
                                    <span v-for="mooring in sticker.moorings">
                                        {{ mooring.name }} ({{ mooring.mooring_bay_name }})
                                    </span>
                                </td>
                            </tr>
                        </tbody>
                    </table> -->

                    <datatable
                        ref="swap_moorings_datatable"
                        :id="datatable_id"
                        :dtOptions="datatable_options"
                        :dtHeaders="datatable_headers"
                    />

                </div>
                <!-- <div class="row form-group">
                    <label class="col-sm-2 control-label" for="reason">Reason</label>
                    <div class="col-sm-9">
                        <textarea class="col-sm-9 form-control" name="reason" v-model="details.reason"></textarea>
                    </div>
                </div> -->
            </div>
            <div slot="footer">
                <div class="row">
                    <div class="col-md-5">
                        <button type="button" v-if="processing" disabled class="btn btn-default" @click="ok"><i class="fa fa-spinner fa-spin"></i> Processing</button>
                        <button type="button" v-else class="btn btn-default" @click="ok" :disabled="!okButtonEnabled">Ok</button>
                        <button type="button" class="btn btn-default" @click="cancel">Cancel</button>
                    </div>
                </div>
            </div>
        </modal>
    </div>
</template>

<script>
import modal from '@vue-utils/bootstrap-modal.vue'
import alert from '@vue-utils/alert.vue'
import { helpers, api_endpoints, constants } from "@/utils/hooks.js"
import datatable from '@/utils/vue/datatable.vue'

export default {
    name:'RequestNewStickerModal',
    components:{
        modal,
        alert,
        datatable,
    },
    props:{
        is_internal: {
            type: Boolean,
            default: false,
        },
        target_email_user_id: {
            type: Number,
            required: false,
            default: 0,
        }
    },
    data:function () {
        let vm = this;
        return {
            approval_id: null,
            stickers: [],
            isModalOpen:false,
            action: '',
            details: vm.getDefaultDetails(),
            processing: false,
            fee_item: null,

            errors: false,
            errorString: '',

            datatable_id: 'swap-moorings-datatable-' + vm._uid,
        }
    },
    watch: {
        approval_id: async function(){
            let vm = this
            // Whenever approval_id is changed, update this.stickers
            if (vm.approval_id){
                const ret = await vm.$http.get(helpers.add_endpoint_json(api_endpoints.approvals, vm.approval_id + '/stickers'))
                for (let sticker of ret.body.stickers){
                    sticker.checked = false
                }
                vm.stickers = ret.body.stickers
                console.log('vm.stickers')
                console.log(vm.stickers)

            } else {
                vm.stickers = []
            }
        }
    },
    computed: {
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
        columnSelect: function() {
            return {
                        // 1. ID
                        data: "id",
                        orderable: false,
                        searchable: false,
                        visible: true,
                        'render': function(row, type, full){
                            return '<input type="radio" name="select" value="' + full.id + '">';
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
                            if (full.migrated){
                                return full.lodgement_number + ' (M)'
                            } else {
                                return full.lodgement_number
                            }
                        },
                        name: 'lodgement_number',
                    }
        },
        columnVesselRegos: function() {
            return {
                data: "id",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function(row, type, full){
                    let ret = ''
                    for (let rego of full.vessel_regos){
                        ret += rego + '<br/>'
                    }
                    return ret
                    //return '';
                },
                name: "current_proposal__vessel_details__vessel__rego_no"
            }
        },
        csrf_token: function() {
          return helpers.getCookie('csrftoken')
        },
        datatable_options: function() {
            let vm = this;
            let selectedColumns = [];
            if (vm.is_internal) {
                selectedColumns = [
                    vm.columnId,
                    vm.columnSelect,
                    vm.columnLodgementNumber,
                    // vm.columnApprovalType,
                    // vm.columnStickerNumber,
                    // vm.columnStickerMailedDate,
                    // vm.columnHolder,
                    // vm.columnStatus,
                    // vm.columnMooring,
                    // vm.columnIssueDate,
                    // vm.columnStartDate,
                    // vm.columnExpiryDate,
                    // vm.columnApprovalLetter,
                    // vm.columnStickerReplacement,
                    vm.columnVesselRegos,
                    // vm.columnGracePeriod,
                    // vm.columnAction,
                ]
            }
            let buttons = []
            // if (vm.is_internal){
            //     buttons = [
            //         {
            //             extend: 'excel',
            //             exportOptions: {
            //                 //columns: ':visible'
            //             }
            //         },
            //         {
            //             extend: 'csv',
            //             exportOptions: {
            //                 //columns: ':visible'
            //             }
            //         },
            //     ]
            // }

            return {
                autoWidth: false,
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                serverSide: true,
                lengthMenu: [ [10, 25, 50, 100, -1], [10, 25, 50, 100, "All"] ],
                //searching: false,
                searching: true,
                ajax: {
                    "url": api_endpoints.approvals_paginated_list + '/list2/?format=datatables&target_email_user_id=' + vm.target_email_user_id,
                    "dataSrc": 'data',
                    "type": 'POST',

                    // adding extra GET params for Custom filtering
                    "data": function ( d ) {
                        d.filter_approval_type = 'ml'
                        // d.show_expired_surrendered = vm.show_expired_surrendered;
                        //d.external_waiting_list = vm.externalWaitingList;
                        //d.filter_status = vm.filterStatus;
                        //d.filter_approval_type2 = vm.filterApprovalType;
                        //d.filter_mooring_bay_id = vm.filterMooringBay;
                        //d.filter_holder_id = vm.filterHolder;
                        // d.max_vessel_length = vm.maxVesselLength;
                        // d.max_vessel_draft = vm.maxVesselDraft;
                        d.csrfmiddlewaretoken = vm.csrf_token
                    }
                },
                //dom: 'frt', //'lBfrtip',
                dom: 'lBfrtip',
                buttons: buttons,
                columns: selectedColumns,
                processing: true,
                initComplete: function() {

                },
                createdRow: function(row, data, dataIndex){
                    if (data.status === 'Current'){
                        if (data.grace_period_details && data.grace_period_details.days_left){
                            let colour_code = '#ff6961'
                            if (data.grace_period_details.days_left > 0){
                                colour_code = '#ffa07a'
                            }
                            $(row).css({
                                'background-color': colour_code
                            })
                        }
                    }
                }
            }
        },
        datatable_headers: function() {
            if (this.is_internal) {
                return [
                    'Id',
                    'Select',
                    'Number',
                    // 'Type',
                    // 'Sticker Number/s',
                    // 'Sticker mailed date',
                    // 'Holder',
                    // 'Status',
                    // 'Mooring',
                    // 'Issue Date',
                    // 'Start Date',
                    // 'Expiry Date',
                    // 'Approval letter',
                    // 'Sticker replacement',
                    'Vessel Rego',
                    // 'Grace period end date',
                ]
            }
        },
        okButtonEnabled: function(){
            if (this.details.reason){
                for (let sticker of this.stickers){
                    if (sticker.checked === true){
                        return true
                    }
                }
            }
            return false
        },
        showError: function() {
            var vm = this;
            return vm.errors;
        },
        title: function() {
            return 'Swap Moorings'
        },
    },
    methods:{
        getDefaultDetails: function(){
            return {
                reason: '',
                date_of_lost_sticker: null,
                date_of_returned_sticker: null,
            }
        },
        ok:function () {
            let vm =this;
            vm.errors = false
            vm.processing = true
            vm.$emit("sendData", {
                //"details": vm.details,
                //"approval_id": vm.approval_id,
                //"stickers": vm.stickers,
                //"waive_the_fee": vm.waive_the_fee,
                "target_approval_id": 594,
            })
        },
        cancel:function () {
            this.close();
        },
        close:function () {
            this.isModalOpen = false
            this.details = this.getDefaultDetails()
            $('#returned_date_elem').val('')
            $('#lost_date_elem').val('')
            this.errors = false
            this.processing = false
            this.approval_id = null
            //$('.has-error').removeClass('has-error');
            //this.validation_form.resetForm();
        },
        addEventListeners: function () {
            let vm = this;
        },
        fetchData: function(){
            let vm = this

            vm.$http.get(api_endpoints.fee_item_sticker_replacement).then(
                (response) => {
                    vm.fee_item = response.body
                },
                (error) => {
                    console.log(error)
                }
            )
        }
    },
    created:function () {
        this.fetchData()
        this.$nextTick(() => {
            this.addEventListeners();
        });
    }
}
</script>

<style lang="css">
</style>
