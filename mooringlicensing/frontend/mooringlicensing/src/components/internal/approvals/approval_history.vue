<template lang="html">
    <div id="approvalHistory">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="title" large>
            <div class="container-fluid">
                <div class="row">
                    <!-- <alert v-if="isApprovalLevelDocument" type="warning"><strong>{{warningString}}</strong></alert> -->
                    <alert :show.sync="showError" type="danger"><strong>{{errorString}}</strong></alert>
                    <div class="col-sm-12">
                        <div class="form-group">
                            <div class="row">
                                <div v-if="approvalId" class="col-lg-12">
                                    <datatable
                                        ref="history_datatable"
                                        :id="datatable_id"
                                        :dtOptions="datatable_options"
                                        :dtHeaders="datatable_headers"
                                    />
                                </div>
                            </div>

                                <!--div class="col-sm-3">
                                    <label class="control-label pull-left" for="mooring_bay">Bay</label>
                                </div>
                                <div class="col-sm-6">
                                    <select class="form-control" v-model="selectedMooringBayId" id="mooring_bay_lookup">
                                        <option v-for="bay in mooringBays" v-bind:value="bay.id">
                                        {{ bay.name }}
                                        </option>
                                    </select>
                                </div-->
                        </div>
                    </div>
                </div>
            </div>

            <div slot="footer">
                <button type="button" class="btn btn-default" @click="ok">Ok</button>
                <button type="button" class="btn btn-default" @click="cancel">Cancel</button>
            </div>
        </modal>
    </div>
</template>

<script>
//import $ from 'jquery'
import modal from '@vue-utils/bootstrap-modal.vue'
//import FileField from '@/components/forms/filefield_immediate.vue'
import alert from '@vue-utils/alert.vue'
import { helpers, api_endpoints, constants } from "@/utils/hooks.js"
import datatable from '@/utils/vue/datatable.vue'

export default {
    name:'approvalHistory',
    components:{
        modal,
        alert,
        datatable,
        //FileField,
    },
    props:{
        approvalId: {
            type: Number,
            required: true,
        },
        /*
        mooringBayId: {
            type: Number,
            required: true,
        },
        */
    },
    data:function () {
        let vm = this;
        return {
            //approvalId: null,
            datatable_id: 'history-datatable-' + vm._uid,
            approvalDetails: {
                approvalLodgementNumber: null,
                //history: {},
            },
            messageDetails: '',
            ccEmail: '',
            isModalOpen:false,
            //state: 'proposed_approval',
            //savingOffer: false,
            validation_form: null,
            errors: false,
            errorString: '',
            successString: '',
            success:false,
            //warningString: 'Please attach Level of Approval document before issuing Approval',
            //siteLicenseeMooring: {},
            //mooringBays: [],
        }
    },
    computed: {
        /*
        waitingListOfferSubmitUrl: function() {
          return `/api/waitinglistallocation/${this.wlaId}/create_mooring_licence_application.json`;
          //return `/api/waitinglistallocation/${this.wlaId}/create_mooring_licence_application/`;
          //return this.submit();
        },
        */
        showError: function() {
            var vm = this;
            return vm.errors;
        },
        title: function(){
            //return this.processing_status == 'With Approver' ? 'Grant' : 'Propose grant';
            let title = "History for ";
            if (this.approvalDetails && this.approvalDetails.approvalLodgementNumber) {
                title += this.approvalDetails.approvalType + ' ';
                title += this.approvalDetails.approvalLodgementNumber;
            }
            return title;
        },
        csrf_token: function() {
          return helpers.getCookie('csrftoken')
        },
        datatable_headers: function(){
            return ['id', 'Lodgement Number', 'Type', 'Sticker Number/s', 'Holder', 'Status', 'Issue Date', 'Reason', 'Approval Letter']
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
        column_lodgement_number: function(){
            return {
                // 2. Lodgement Number
                data: "id",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function(row, type, full){
                    return full.approval_lodgement_number
                },
                //name: 'lodgement_number',
            }
        },
        column_type: function(){
            return {
                // 3. Type (This corresponds to the 'ApplicationType' at the backend)
                data: "id",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function(row, type, full){
                    return full.approval_type_description;
                }
            }
        },
        column_sticker_numbers: function(){
            return {
                // 3. Type (This corresponds to the 'ApplicationType' at the backend)
                data: "id",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function(row, type, full){
                    return full.sticker_numbers;
                }
            }
        },

        column_holder: function(){
            return {
                // 3. Type (This corresponds to the 'ApplicationType' at the backend)
                data: "id",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function(row, type, full){
                    return full.holder;
                }
            }
        },
        column_approval_status: function(){
            return {
                // 3. Type (This corresponds to the 'ApplicationType' at the backend)
                data: "id",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function(row, type, full){
                    return full.approval_status;
                }
            }
        },
        column_start_date: function(){
            return {
                // 3. Type (This corresponds to the 'ApplicationType' at the backend)
                data: "id",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function(row, type, full){
                    return full.start_date_str
                }
            }
        },
        column_reason: function(){
            return {
                // 3. Type (This corresponds to the 'ApplicationType' at the backend)
                data: "id",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function(row, type, full){
                    return full.reason;
                }
            }
        },
        column_approval_letter: function(){
            return {
                // 3. Type (This corresponds to the 'ApplicationType' at the backend)
                data: "id",
                orderable: true,
                searchable: true,
                visible: true,
                'render': function(row, type, full){
                    //return full.approval_letter;
                    //return '';
                    return `<div><a href='${full.approval_letter}' target='_blank'><i style='color:red;' class='fa fa-file-pdf-o'></i></a></div>`;
                }
            }
        },

        datatable_options: function(){
            let vm = this
            let columns = [
                vm.column_id,
                vm.column_lodgement_number,
                vm.column_type,
                vm.column_sticker_numbers,
                vm.column_holder,
                vm.column_approval_status,
                vm.column_start_date,
                vm.column_reason,
                vm.column_approval_letter,
            ]

            return {
                autoWidth: false,
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                //serverSide: true,
                searching: true,
                ordering: true,
                order: [[0, 'desc']],
                ajax: {
                    //"url": api_endpoints.proposals_paginated_list + '?format=datatables',
                    "url": api_endpoints.lookupApprovalHistory(this.approvalId),
                    "dataSrc": 'data',

                    // adding extra GET params for Custom filtering
                    "data": function ( d ) {
                        /*
                        d.filter_application_type = vm.filterApplicationType
                        d.filter_application_status = vm.filterApplicationStatus
                        d.filter_applicant = vm.filterApplicant
                        d.level = vm.level
                        */
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
    methods:{
        ok: async function() {
            //await this.sendData();
            this.close()
        },
        cancel:function () {
            this.close()
        },
        close: function () {
            this.isModalOpen = false;
            this.errors = false;
            $('.has-error').removeClass('has-error');
            //this.validation_form.resetForm();
        },
        fetchApprovalDetails: async function() {
            const res = await this.$http.get(api_endpoints.lookupApprovalDetails(this.approvalId));
            if (res.ok) {
                this.approvalDetails = Object.assign({}, res.body);
            }
        },
        /*
        eventListeners:function (){
            let vm = this;
        },
        */
        /*
        readRiaMooring: function() {
            let vm = this;
            if (vm.approval.ria_mooring_name) {
                console.log("read ria mooring")
                var option = new Option(vm.approval.ria_mooring_name, vm.approval.ria_mooring_name, true, true);
                $(vm.$refs.mooring_lookup).append(option).trigger('change');
            }
        },
        */

    },
    mounted:function () {
        this.$nextTick(()=>{
            //this.initialiseMooringLookup();

        });
    },
    created: function() {
        this.$nextTick(()=>{
            this.fetchApprovalDetails();
            //this.fetchMooringBays();
            //this.selectedMooringBayId = this.mooringBayId;
        });
    },
}
</script>

<style lang="css">
</style>
