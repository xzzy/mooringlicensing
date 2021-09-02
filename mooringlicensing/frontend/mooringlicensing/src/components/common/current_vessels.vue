<template lang="html">
    <div id="current_vessels">
        <FormSection v-if="mooringLicenceCurrentVesselDisplayText || currentVesselDisplayText" label="Current Vessel" Index="current_vessel">
            <div v-if="mooringLicenceCurrentVesselDisplayText" class="row form-group">
                <div class="col-sm-9">
                    {{ mooringLicenceCurrentVesselDisplayText }}
                </div>
            </div>
            <div v-else class="row form-group">
                <div class="col-sm-9">
                    <label for="" class="col-sm-12 control-label">{{ currentVesselDisplayText }}</label>
                        <div class="col-sm-9">
                            <input 
                            @change="resetCurrentVessel" 
                            :disabled="readonly" 
                            type="radio" 
                            id="current_vessel_true" 
                            name="current_vessel_true" 
                            :value="true" 
                            v-model="keep_current_vessel" 
                            required
                            />
                            <label for="current_vessel_true" class="control-label">Keep my current vessel</label>
                        </div>
                        <div class="col-sm-9">
                            <input 
                            @change="resetCurrentVessel" 
                            :disabled="readonly" 
                            type="radio" 
                            id="current_vessel_false" 
                            name="current_vessel_false" 
                            :value="false" 
                            v-model="keep_current_vessel" 
                            required
                            />
                            <label for="current_vessel_false" class="control-label">Change to different vessel</label>
                        </div>

                </div>
            </div>
        </FormSection>
    </div>

</template>
<script>
import Vue from 'vue'
import FormSection from '@/components/forms/section_toggle.vue'
var select2 = require('select2');
require("select2/dist/css/select2.min.css");
require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'

    export default {
        name:'current_vessels',
        data:function () {
            return {
                keep_current_vessel: true,
            }
        },
        components:{
            FormSection,
        },
        props:{
            proposal:{
                type: Object,
                required:true
            },
            readonly:{
                type: Boolean,
                default: true,
            },
            is_internal:{
              type: Boolean,
              default: false
            },
        },
        computed: {
            mooringLicenceCurrentVesselDisplayText: function() {
                let displayText = '';
                if (this.proposal && this.proposal.mooring_licence_vessels && this.proposal.mooring_licence_vessels.length) {
                    displayText += `Your mooring licence ${this.proposal.approval_lodgement_number} 
                    currently lists the following vessels ${this.proposal.mooring_licence_vessels.toString()}.`;
                }
                return displayText;
            },
            currentVesselDisplayText: function() {
                let displayText = '';
                if (this.proposal && this.proposal.approval_vessel_rego_no) {
                    displayText += `Your ${this.proposal.approval_type_text} ${this.proposal.approval_lodgement_number} 
                    lists a vessel with registration number ${this.proposal.approval_vessel_rego_no}.`;
                }
                /*
                if (this.proposal && this.proposal.mooring_licence_vessels && this.proposal.mooring_licence_vessels.length) {
                    displayText += `Your Authorised User Permit ${this.proposal.approval_lodgement_number} 
                    lists the following vessel ${this.proposal.mooring_licence_vessels.toString()}.`;
                }
                */
                return displayText;
            },

        },
        methods:{
            resetCurrentVessel: function() {
                this.$nextTick(() => {
                    this.$emit("resetCurrentVessel", this.keep_current_vessel)
                });
            },
        },
        mounted: function () {
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

