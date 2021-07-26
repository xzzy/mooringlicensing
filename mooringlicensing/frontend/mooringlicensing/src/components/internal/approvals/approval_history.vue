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
            </div>

            <!--div slot="footer">
                <button type="button" v-if="savingOffer" disabled class="btn btn-default" @click="ok"><i class="fa fa-spinner fa-spin"></i> Processing</button>
                <button type="button" v-else class="btn btn-default" @click="ok">Ok</button>
                <button type="button" class="btn btn-default" @click="cancel">Cancel</button>
            </div-->
        </modal>
    </div>
</template>

<script>
//import $ from 'jquery'
import modal from '@vue-utils/bootstrap-modal.vue'
//import FileField from '@/components/forms/filefield_immediate.vue'
import alert from '@vue-utils/alert.vue'
import { helpers, api_endpoints, constants } from "@/utils/hooks.js"

export default {
    name:'approvalHistory',
    components:{
        modal,
        alert,
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
            approvalHistory: {
                approvalLodgementNumber: null,
                history: {},
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
            if (this.approvalHistory && this.approvalHistory.approvalLodgementNumber) {
                title += this.approvalHistory.approvalType + ' ';
                title += this.approvalHistory.approvalLodgementNumber;
            }
            return title;
        },
        csrf_token: function() {
          return helpers.getCookie('csrftoken')
        },
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
        fetchApprovalHistory: async function() {
            const res = await this.$http.get(api_endpoints.lookupApprovalHistory(this.approvalId));
            console.log(res);
            if (res.ok) {
                this.approvalHistory = Object.assign({}, res.body);
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
            this.fetchApprovalHistory();
            //this.fetchMooringBays();
            //this.selectedMooringBayId = this.mooringBayId;
        });
    },
}
</script>

<style lang="css">
</style>
