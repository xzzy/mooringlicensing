<template lang="html">
    <div id="vessels">
        <FormSection label="Registration Details" Index="registration_details">
            <div class="row form-group">
                <label for="vessel_search" class="col-sm-3 control-label">Vessel registration number</label>
                <div class="col-sm-9">
                    <select :disabled="readonly" id="vessel_search"  ref="vessel_rego_nos" class="form-control" style="width: 40%">
                        <!--option value="null"></option>
                        <option v-for="rego in vesselRegoNos" :value="rego">{{rego}}</option-->
                    </select>
                </div>
            </div>
            <!--div class="row form-group">
                <label for="" class="col-sm-3 control-label">Vessel registration number</label>
                <div class="col-sm-9">
                    <input :readonly="!editableVessel" type="text" class="form-control" id="vessel_registration_number" placeholder="" v-model="vessel.rego_no" required=""/>
                </div>
            </div-->
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Vessel name</label>
                <div class="col-sm-9">
                    <input :readonly="!editableVesselDetails" type="text" class="form-control" id="vessel_name" placeholder="" v-model="vessel.vessel_details.vessel_name" required/>
                </div>
            </div>
            <!--div v-if="!vessel.read_only" class="row form-group"-->
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Registration vessel owner</label>
                <div class="col-sm-9">
                    <div class="row">
                        <div class="col-sm-9">
                            <input :disabled="readonly" type="radio" id="registered_owner_current_user" :value="true" v-model="vessel.vessel_ownership.individual_owner" required/>
                            <label for="registered_owner_current_user" class="control-label">{{  profileFullName }}</label>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-sm-3">
                            <input :disabled="readonly" type="radio" id="registered_owner_company" name="registered_owner_company" :value="false" v-model="vessel.vessel_ownership.individual_owner" required=""/>
                            <label for="registered_owner_company" class="control-label">Your company</label>
                        </div>
                        <div v-if="companyOwner" class="col-sm-8">
                            <input :readonly="readonly" type="text" class="form-control" id="registered_owner_company_name" placeholder="Company name" v-model="vessel.vessel_ownership.org_name" required=""/>
                        </div>
                    </div>
                </div>
            </div>
            <!--div v-else class="row form-group">
                <label for="" class="col-sm-3 control-label">Registration vessel owner</label>
                <div class="col-sm-9">
                    <div class="row">
                        <div class="col-sm-9">
                            {{   registeredOwner }}
                        </div>
                    </div>
                </div>
            </div-->
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Ownership percentage</label>
                <div class="col-sm-2">
                    <input 
                     :readonly="readonly" 
                    type="number" 
                    step="1"
                    min="25" 
                    max="100" 
                    class="form-control" 
                    id="ownership_percentage" 
                    placeholder="" 
                    v-model="vessel.vessel_ownership.percentage" 
                    required=""
                    />
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Permanent or usual place of berthing/mooring of vessel</label>
                <!--label for="" class="col-sm-3 control-label">Permanent or usual place</label-->
                <div class="col-sm-9">
                    <input :readonly="!editableVesselDetails" type="text" class="col-sm-9 form-control" id="berth_mooring" placeholder="" v-model="vessel.vessel_details.berth_mooring" required=""/>
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Copy of DoT registration papers</label>
                <div class="col-sm-9">
                    <FileField 
                        :readonly="readonly"
                        ref="vessel_registration_documents"
                        name="vessel-registration-documents"
                        :isRepeatable="true"
                        :documentActionUrl="vesselRegistrationDocumentUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
            <div v-if="applicationTypeCodeMLA" class="row form-group">
                <label for="" class="col-sm-3 control-label">Certified Hull Identification Number (HIN), if not already provided on the registration papers</label>
                <div class="col-sm-9">
                    <FileField 
                        :readonly="readonly"
                        ref="hull_identification_number_documents"
                        name="hull-identification-number-documents"
                        :isRepeatable="true"
                        :documentActionUrl="hullIdentificationNumberDocumentUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

        </FormSection>
        <FormSection label="Vessel Details" Index="vessel_details">
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Vessel length</label>
                <div class="col-sm-2">
                    <input :readonly="!editableVesselDetails" type="number" min="1" class="form-control" id="vessel_length" placeholder="" v-model="vessel.vessel_details.vessel_length" required=""/>
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Overall length of vessel</label>
                <div class="col-sm-2">
                    <input :readonly="!editableVesselDetails" type="number" min="1" class="form-control" id="overall_length" placeholder="" v-model="vessel.vessel_details.vessel_overall_length" required=""/>
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Displacement tonnage</label>
                <div class="col-sm-2">
                    <input :readonly="!editableVesselDetails" type="number" min="1" class="form-control" id="displacement_tonnage" placeholder="" v-model="vessel.vessel_details.vessel_weight" required=""/>
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Draft</label>
                <div class="col-sm-2">
                    <input :readonly="!editableVesselDetails" type="number" min="1" class="form-control" id="draft" placeholder="" v-model="vessel.vessel_details.vessel_draft" required=""/>
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Vessel Type</label>
                <div class="col-sm-4">
                    <select :readonly="!editableVesselDetails" class="form-control" style="width:40%" v-model="vessel.vessel_details.vessel_type">
                        <option v-for="vesselType in vesselTypes" :value="vesselType.code">
                            {{ vesselType.description }}
                        </option>
                    </select>
                </div>
            </div>
        </FormSection>
    </div>

</template>
<script>
import Vue from 'vue'
import FormSection from '@/components/forms/section_toggle.vue'
import FileField from '@/components/forms/filefield_immediate.vue'
var select2 = require('select2');
require("select2/dist/css/select2.min.css");
require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'

    export default {
        name:'vessels',
        data:function () {
            return {
                vessel: {
                    vessel_details: {},
                    vessel_ownership: {
                        //registered_owner: 'current_user',
                    }
                },
                vesselTypes: [],
                vesselRegoNos: [],
                selectedRego: null,
            }
        },
        components:{
            FormSection,
            FileField,
        },
        props:{
            proposal:{
                type: Object,
                //required:true
            },
            profile:{
                type: Object,
                required:true
            },
            readonly:{
                type: Boolean,
                default: true,
            },
            creatingVessel:{
                type: Boolean,
            },
        },
        computed: {
            companyOwner: function() {
                //let returnVal = false;
                if (this.vessel && this.vessel.vessel_ownership && this.vessel.vessel_ownership.individual_owner === false) {
                    //returnVal = this.vessel.vessel_ownership.individual_owner;
                    return true;
                }
                //return returnVal;
            },
            registeredOwner: function() {
                if (this.vessel && this.vessel.vessel_ownership) {
                    return this.vessel.vessel_ownership.registered_owner;
                }
            },
            editableVesselDetails: function() {
                let retVal = false;
                if (this.creatingVessel) {
                    retVal = true;
                } else if (!this.readonly) {
                    // front-end lookup 
                    if (this.vessel.vessel_details.hasOwnProperty('read_only')) {
                        retVal = !this.vessel.vessel_details.read_only;
                    // vessel stored on Proposal
                    } else if (this.proposal) {
                        retVal = this.proposal.editable_vessel_details;
                    }
                }
                return retVal;
            },
            profileFullName: function() {
                if (this.profile) {
                    return this.profile.full_name;
                }
            },
            fee_invoice_url: function(){
                return this.fee_paid ? this.proposal.fee_invoice_url : '';
            },
            vesselRegistrationDocumentUrl: function() {
                let url = '';
                if (this.proposal && this.proposal.id) {
                    url = helpers.add_endpoint_join(
                        api_endpoints.proposal,
                        this.proposal.id + '/process_vessel_registration_document/'
                    )
                }
                return url;
            },
            hullIdentificationNumberDocumentUrl: function() {
                let url = '';
                if (this.proposal && this.proposal.id) {
                    url = helpers.add_endpoint_join(
                        api_endpoints.proposal,
                        this.proposal.id + '/process_hull_identification_number_document/'
                    )
                }
                return url;
            },
            applicationTypeCodeMLA: function() {
                if (this.proposal && this.proposal.application_type_code==='mla') {
                    return true;
                }
            },

        },
        methods:{
            /*
            validateVesselReg: function() {
                let vm = this;
                vm.vesselReg = vm.vesselReg.toUpperCase();
                vm.vesselReg = vm.vesselReg.replace(/\s/g,"");
                vm.vesselReg = vm.vesselReg.replace(/\W/g,"");
                */

            matcherFunction: function(params, data) {
                console.log(params);
                console.log(data);
            },
            initialiseSelects: function(){
                let vm = this;
                $(vm.$refs.vessel_rego_nos).select2({
                    minimumInputLength: 2,
                    "theme": "bootstrap",
                    allowClear: true,
                    placeholder:"Select Vessel Registration",
                    tags: true,
                    createTag: function (tag) {
                        return {
                            id: tag.term,
                            text: tag.term,
                            tag: true
                        };
                    },
                    ajax: {
                        url: api_endpoints.vessel_rego_nos,
                        dataType: 'json',
                    },
                    matcher: vm.matcherFunction,
                }).
                on("select2:select",function (e) {
                    var selected = $(e.currentTarget);
                    // force uppercase and no whitespace
                    let data = e.params.data.id;
                    console.log(data)
                    data = data.toUpperCase();
                    data = data.replace(/\s/g,"");
                    data = data.replace(/\W/g,"");
                    vm.$nextTick(() => {
                        //if (!isNew) {
                        if (!e.params.data.tag) {
                            console.log("fetch new vessel");
                            // fetch draft/approved vessel
                            vm.lookupVessel(data);
                        } else {
                            vm.vessel = Object.assign({}, 
                                {   
                                    new_vessel: true,
                                    rego_no: data,
                                    vessel_details: {
                                        read_only: false,
                                    },
                                    vessel_ownership: {
                                        registered_owner: 'current_user',
                                    }
                                });
                        }
                    });
                }).
                on("select2:unselect",function (e) {
                    var selected = $(e.currentTarget);
                    vm.vessel.rego_no = '';
                    vm.vessel = Object.assign({}, 
                        {   
                            vessel_details: {
                                read_only: false,
                            },
                            vessel_ownership: {
                                registered_owner: 'current_user',
                            }
                        });
                }).
                on("select2:open",function (e) {
                    const searchField = $(".select2-search__field")
                    console.log(searchField);
                    searchField[0].focus();
                    // prevent spacebar from being used
                    searchField.on("keydown",function (e) {
                        if ([32,].includes(e.which)) {
                            e.preventDefault();
                            return false;
                        }
                    });
                });
                // read vessel.rego_no if exists on vessel.vue open
                vm.readRegoNo();
            },
            addEventListeners: function() {
                let vm = this;
                $('#ownership_percentage').on('keydown', (e) => {
                    if ([190, 110].includes(e.which)) {
                        e.preventDefault();
                        return false;
                    }
                });
            },
            /*
            fetchVesselRegoNos: async function() {
                const response = await this.$http.get(api_endpoints.vessel_rego_nos);
                for (let rego of response.body) {
                    this.vesselRegoNos.push(rego)
                }
            },
            */
            readRegoNo: function() {
                let vm = this;
                if (vm.vessel.rego_no) {
                    var option = new Option(vm.vessel.rego_no, vm.vessel.rego_no, true, true);
                    $(vm.$refs.vessel_rego_nos).append(option).trigger('change');
                }
            },
            fetchVesselTypes: async function(){
                const response = await this.$http.get(api_endpoints.vessel_types_dict);
                for (let vessel_type of response.body) {
                    this.vesselTypes.push(vessel_type)
                }
            },
            lookupVessel: async function(id) {
                const res = await this.$http.get(api_endpoints.lookupVessel(id));
                const vesselData = res.body;
                console.log(res);
                if (vesselData && vesselData.rego_no) {
                    this.vessel = Object.assign({}, vesselData);
                }
            },
            fetchVessel: async function() {
                if (this.proposal.processing_status === 'Draft' && !this.proposal.vessel_details_id) {
                    this.vessel.rego_no = this.proposal.rego_no;
                    this.vessel.vessel_id = this.proposal.vessel_id;
                    let vessel_details = {};
                    vessel_details.vessel_type = this.proposal.vessel_type;
                    vessel_details.vessel_name = this.proposal.vessel_name;
                    vessel_details.vessel_overall_length = this.proposal.vessel_overall_length;
                    vessel_details.vessel_length = this.proposal.vessel_length;
                    vessel_details.vessel_draft = this.proposal.vessel_draft;
                    vessel_details.vessel_beam = this.proposal.vessel_beam;
                    vessel_details.vessel_weight = this.proposal.vessel_weight;
                    vessel_details.berth_mooring = this.proposal.berth_mooring;
                    let vessel_ownership = {};
                    vessel_ownership.org_name = this.proposal.org_name;
                    vessel_ownership.percentage = this.proposal.percentage;
                    vessel_ownership.individual_owner = this.proposal.individual_owner;
                    this.vessel.vessel_details = Object.assign({}, vessel_details);
                    this.vessel.vessel_ownership = Object.assign({}, vessel_ownership);
                } else {
                    let url = '';
                    if (this.proposal && this.proposal.id && this.proposal.vessel_details_id) {
                        url = helpers.add_endpoint_join(
                            //'/api/proposal/',
                            api_endpoints.proposal,
                            this.proposal.id + '/fetch_vessel/'
                        )
                    }
                    await this.fetchSubmittedVesselCommon(url);
                }
            },
            fetchSubmittedVesselCommon: async function(url) {
                const res = await this.$http.get(url);
                const vesselData = res.body;
                if (vesselData && vesselData.rego_no) {
                    this.vessel = Object.assign({}, vesselData);
                }
                this.readRegoNo();
            },
        },
        mounted: function () {
            this.$nextTick(async () => {
                await this.fetchVesselTypes();
                //await this.fetchVesselRegoNos();
                if (this.proposal) {
                    await this.fetchVessel();
                } else if (!this.creatingVessel) {
                    const url = api_endpoints.lookupVesselOwnership(this.$route.params.id);
                    this.fetchSubmittedVesselCommon(url);
                }
                this.initialiseSelects();
                this.addEventListeners();
            });
        },
        created: function() {
        },
    }
</script>

<style lang="css" scoped>
    input[type=text] {
        padding-left: 1em;
    }
</style>

