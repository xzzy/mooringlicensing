<template lang="html">

    <div id="vessels">
        <FormSection label="Registration Details">
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Vessel registration number</label>
                <div class="col-sm-9">
                    <input readonly="!editableVessel" type="text" class="form-control" id="vessel_registration_number" placeholder="" v-model="vessel.rego_no" required=""/>
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Vessel name</label>
                <div class="col-sm-9">
                    <input readonly="editableVessel" type="text" class="form-control" id="vessel_name" placeholder="" v-model="vessel.vessel_details.vessel_name" required=""/>
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Registration vessel owner</label>
                <div class="col-sm-9">
                    <div class="row">
                        <div class="col-sm-9">
                            <input type="radio" name="registered_owner_current_user" value="current_user" v-model="vessel.vessel_ownership.registered_owner" required="">
                                {{   profileFullName }}
                            </input>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-sm-2">
                            <input type="radio" id="registered_owner_company" name="registered_owner_company" value="company_name" v-model="vessel.vessel_ownership.registered_owner" required="">
                            Your company
                            </input>
                        </div>
                        <div class="col-sm-8">
                            <input type="text" class="form-control" id="registered_owner_company_name" placeholder="" v-model="vessel.vessel_ownership.registered_owner_company_name" required=""/>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Ownership percentage</label>
                <div class="col-sm-2">
                    <input type="number" min="1" max="100" class="form-control" id="ownership_percentage" placeholder="" v-model="vessel.vessel_ownership.percentage" required=""/>
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Permanent or usual place of berthing/mooring of vessel</label>
                <!--label for="" class="col-sm-3 control-label">Permanent or usual place</label-->
                <div class="col-sm-9">
                    <input type="text" class="col-sm-9 form-control" id="berth_mooring" placeholder="" v-model="vessel.vessel_ownership.berth_mooring" required=""/>
                </div>
            </div>
            <div class="row form-group">
            <!--div class="form-group"-->
                <label for="" class="col-sm-3 control-label">Copy of DoT registration papers</label>
                <div class="col-sm-9">
                    <FileField
                        ref="vessel_registration_documents"
                        name="vessel-registration-documents"
                        :isRepeatable="true"
                        :documentActionUrl="vesselRegistrationDocumentUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            <!--/div-->
            </div>
        </FormSection>
        <FormSection label="Vessel Details">
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Vessel length</label>
                <div class="col-sm-2">
                    <input type="number" min="1" class="form-control" id="vessel_length" placeholder="" v-model="vessel.vessel_details.vessel_length" required=""/>
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Overall length of vessel</label>
                <div class="col-sm-2">
                    <input type="number" min="1" class="form-control" id="overall_length" placeholder="" v-model="vessel.vessel_details.vessel_overall_length" required=""/>
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Displacement tonnage</label>
                <div class="col-sm-2">
                    <input type="number" min="1" class="form-control" id="displacement_tonnage" placeholder="" v-model="vessel.vessel_details.vessel_weight" required=""/>
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Draft</label>
                <div class="col-sm-2">
                    <input type="number" min="1" class="form-control" id="draft" placeholder="" v-model="vessel.vessel_details.vessel_draft" required=""/>
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Vessel Type</label>
                <div class="col-sm-4">
                    <select class="form-control" style="width:40%" v-model="vessel.vessel_details.vessel_type">
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
                        registered_owner: 'current_user',
                    }
                },
                vesselTypes: [],
            }
        },
        components:{
            FormSection,
            FileField,
        },
        props:{
            proposal:{
                type: Object,
                required:true
            },
            profile:{
                type: Object,
                required:true
            }
        },
        computed: {
            editableVessel: function() {
                if (this.proposal) {
                    return this.proposal.editable_vessel;
                }
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
                        '/api/proposal/',
                        this.proposal.id + '/process_vessel_registration_document/'
                    )
                }
                return url;
            },

        },
        methods:{
            fetchVesselTypes: function(){
                this.$http.get(api_endpoints.vessel_types_dict).then((response) => {
                    for (let vessel_type of response.body) {
                        this.vesselTypes.push(vessel_type)
                    }
                },(error) => {
                    console.log(error);
                })
            },
            // modify this
            fetchVessel: async function() {
                let url = '';
                if (this.proposal && this.proposal.id) {
                    url = helpers.add_endpoint_join(
                        '/api/proposal/',
                        this.proposal.id + '/fetch_vessel/'
                    )
                }
                const res = await this.$http.get(url);
                const vesselData = res.body;
                if (vesselData && vesselData.rego_no) {
                    this.vessel = Object.assign({}, vesselData);
                }
                if (!this.vessel.vessel_ownership.registered_owner) {
                    this.vessel.vessel_ownership.registered_owner = 'current_user';
                }
            },
        },
        mounted:function () {
        },
        created: function() {
            this.fetchVesselTypes();
            this.fetchVessel();
        },
    }
</script>

<style lang="css" scoped>
</style>

