<template lang="html">
    <div id="offerMooringLicence">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="title" large>
            <div class="container-fluid">
                <div class="row">
                    <!-- <alert v-if="isApprovalLevelDocument" type="warning"><strong>{{warningString}}</strong></alert> -->
                    <alert :show.sync="showError" type="danger"><strong>{{errorString}}</strong></alert>
                    <div class="col-sm-12">
                        <div class="form-group">
                            <div class="row">
                                <div class="col-sm-3">
                                    <label class="control-label pull-left" for="mooring_bay">Bay</label>
                                </div>
                                <div class="col-sm-6">
                                    <select class="form-control" v-model="selectedMooringBayId" id="mooring_bay_lookup">
                                        <option v-for="bay in mooringBays" v-bind:value="bay.id">
                                        {{ bay.name }}
                                        </option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div class="form-group">
                            <div class="row">
                                <div class="col-sm-3">
                                    <label class="control-label pull-left" for="mooring_site_id">Mooring Site ID</label>
                                </div>
                                <div class="col-sm-6">
                                    <select 
                                        id="mooring_lookup"  
                                        name="mooring_lookup"  
                                        ref="mooring_lookup" 
                                        class="form-control" 
                                    />
                                </div>
                            </div>
                        </div>
                        <div class="form-group">
                            <div class="row">
                                <div class="col-sm-3">
                                    <label class="control-label pull-left"  for="Name">Details</label>
                                </div>
                                <div class="col-sm-9">
                                    <textarea name="approval_details" class="form-control" style="width:70%;" v-model="messageDetails"></textarea>
                                </div>
                            </div>
                        </div>
                        <div class="form-group">
                            <div class="row">
                                <div class="col-sm-3">
                                    <label class="control-label pull-left"  for="Name">BCC email</label>
                                </div>
                                <div class="col-sm-9">
                                        <input type="text" class="form-control" name="approval_cc" style="width:70%;" ref="bcc_email" v-model="ccEmail">
                                </div>
                            </div>
                        </div>
                        <div class="form-group">
                            <div class="row">
                                <div class="col-sm-12">
                                    <label class="control-label pull-left"  for="Name">Document</label>
                                </div>

                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div slot="footer">
                <button type="button" v-if="savingOffer" disabled class="btn btn-default" @click="ok"><i class="fa fa-spinner fa-spin"></i> Processing</button>
                <button type="button" v-else class="btn btn-default" @click="ok">Ok</button>
                <button type="button" class="btn btn-default" @click="cancel">Cancel</button>
            </div>
        </modal>
    </div>
</template>

<script>
//import $ from 'jquery'
import modal from '@vue-utils/bootstrap-modal.vue'
import alert from '@vue-utils/alert.vue'
import { helpers, api_endpoints, constants } from "@/utils/hooks.js"

export default {
    name:'OfferMooringLicence',
    components:{
        modal,
        alert
    },
    props:{
        wlaId: {
            type: Number,
            required: true,
        },
    },
    data:function () {
        let vm = this;
        return {
            messageDetails: '',
            ccEmail: '',
            selectedMooringBayId: null,
            isModalOpen:false,
            state: 'proposed_approval',
            savingOffer: false,
            validation_form: null,
            errors: false,
            errorString: '',
            successString: '',
            success:false,
            //warningString: 'Please attach Level of Approval document before issuing Approval',
            //siteLicenseeMooring: {},
            mooringBays: [],
        }
    },
    computed: {
        showError: function() {
            var vm = this;
            return vm.errors;
        },
        title: function(){
            //return this.processing_status == 'With Approver' ? 'Grant' : 'Propose grant';
            return "Offer Mooring Licence";
        },
        csrf_token: function() {
          return helpers.getCookie('csrftoken')
        },
    },
    methods:{
        post_and_redirect: function(url, postData) {
            /* http.post and ajax do not allow redirect from Django View (post method),
               this function allows redirect by mimicking a form submit.
               usage:  vm.post_and_redirect(vm.application_fee_url, {'csrfmiddlewaretoken' : vm.csrf_token});
            */
            var postFormStr = "<form method='POST' target='_blank' name='Preview Licence' action='" + url + "'>";
            for (var key in postData) {
                if (postData.hasOwnProperty(key)) {
                    postFormStr += "<input type='hidden' name='" + key + "' value='" + postData[key] + "'>";
                }
            }
            postFormStr += "</form>";
            var formElement = $(postFormStr);
            $('body').append(formElement);
            $(formElement).submit();
        },
        ok:function () {
            let vm =this;
            if($(vm.form).valid()){
                vm.sendData();
                //vm.$router.push({ path: '/internal' });
            }
        },
        cancel:function () {
            this.close()
        },
        close:function () {
            this.isModalOpen = false;
            this.errors = false;
            $('.has-error').removeClass('has-error');
            //this.validation_form.resetForm();
        },
        fetchMooringBays: async function() {
            const res = await this.$http.get(api_endpoints.mooring_bays);
            for (let bay of res.body) {
                this.mooringBays.push(bay)
            }
        },
        /*
        fetchSiteLicenseeMooring: async function() {
            const res = await this.$http.get(`${api_endpoints.mooring}${this.proposal.mooring_id}`);
            this.siteLicenseeMooring = Object.assign({}, res.body);
        },

        fetchContact: function(id){
            let vm = this;
            vm.$http.get(api_endpoints.contact(id)).then((response) => {
                vm.contact = response.body; vm.isModalOpen = true;
            },(error) => {
                console.log(error);
            } );
        },
        */
        sendData:function(){
            let vm = this;
            vm.errors = false;
            let approval = JSON.parse(JSON.stringify(vm.approval));

            vm.issuingApproval = true;
            if (vm.state == 'proposed_approval'){
                vm.$http.post(helpers.add_endpoint_json(api_endpoints.proposal,vm.proposal_id + '/proposed_approval'),JSON.stringify(approval),{
                        emulateJSON:true,
                    }).then((response)=>{
                        vm.issuingApproval = false;
                        vm.close();
                        vm.$emit('refreshFromResponse',response);
                        vm.$router.push({ path: '/internal' }); //Navigate to dashboard page after Propose issue.

                    },(error)=>{
                        vm.errors = true;
                        vm.issuingApproval = false;
                        vm.errorString = helpers.apiVueResourceError(error);
                    });
            }
            else if (vm.state == 'final_approval'){
                console.log('final_approval in proposed_issuance.vue')
                vm.$http.post(helpers.add_endpoint_json(api_endpoints.proposal,vm.proposal_id+'/final_approval'),JSON.stringify(approval),{
                        emulateJSON:true,
                    }).then((response)=>{
                        vm.issuingApproval = false;
                        vm.close();
                        vm.$emit('refreshFromResponse', response);
                    },(error)=>{
                        vm.errors = true;
                        vm.issuingApproval = false;
                        vm.errorString = helpers.apiVueResourceError(error);
                    });
            }

        },
        addFormValidations: function() {
            let vm = this;
            vm.validation_form = $(vm.form).validate({
                rules: {
                    //start_date:"required",
                    //due_date:"required",
                    approval_details:"required",
                },
                messages: {
                },
                showErrors: function(errorMap, errorList) {
                    $.each(this.validElements(), function(index, element) {
                        var $element = $(element);
                        $element.attr("data-original-title", "").parents('.form-group').removeClass('has-error');
                    });
                    // destroy tooltips on valid elements
                    $("." + this.settings.validClass).tooltip("destroy");
                    // add or update tooltips
                    for (var i = 0; i < errorList.length; i++) {
                        var error = errorList[i];
                        $(error.element)
                            .tooltip({
                                trigger: "focus"
                            })
                            .attr("data-original-title", error.message)
                            .parents('.form-group').addClass('has-error');
                    }
                }
            });
       },
       eventListeners:function () {
            let vm = this;
       },
        initialiseMooringLookup: function(){
            let vm = this;
            $(vm.$refs.mooring_lookup).select2({
                minimumInputLength: 2,
                "theme": "bootstrap",
                allowClear: true,
                placeholder:"Select Mooring",
                ajax: {
                    url: api_endpoints.mooring_lookup_per_bay,
                    //url: api_endpoints.vessel_rego_nos,
                    dataType: 'json',
                    data: function(params) {
                        var query = {
                            term: params.term,
                            type: 'public',
                            mooring_bay_id: vm.selectedMooringBayId,
                        }
                        return query;
                    },
                },
            }).
            on("select2:select", function (e) {
                var selected = $(e.currentTarget);
                let data = e.params.data.id;
                vm.selectedMooringId = data;
            }).
            on("select2:unselect",function (e) {
                var selected = $(e.currentTarget);
                vm.selectedMooringId = null;
            }).
            on("select2:open",function (e) {
                //const searchField = $(".select2-search__field")
                const searchField = $('[aria-controls="select2-mooring_lookup-results"]')
                // move focus to select2 field
                searchField[0].focus();
            });
            //vm.readRiaMooring();
            // clear mooring lookup on Mooring Bay change
            $('#mooring_bay_lookup').on('change', function() {
                $(vm.$refs.mooring_lookup).val(null).trigger('change');
            });
        },
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
        let vm =this;
        //vm.form = document.forms.approvalForm;
        vm.addFormValidations();
        this.$nextTick(()=>{
            //vm.eventListeners();
            //this.approval = Object.assign({}, this.proposal.proposed_issuance_approval);
            this.initialiseMooringLookup();

        });
    },
    created: function() {
        this.$nextTick(()=>{
            this.fetchMooringBays();
            /*
            if (this.siteLicensee) {
                this.fetchSiteLicenseeMooring();
            }
            */
        });
    },
}
</script>

<style lang="css">
</style>
