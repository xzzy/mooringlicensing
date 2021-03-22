<template lang="html">

    <div class="row">
        <div class="col-sm-12" id="vessels">
        <FormSection label="Registration Details">
            <div class="form-group">
                <label for="" class="col-sm-3 control-label">Vessel registration number</label>
                <div class="col-sm-9">
                    <input type="text" class="form-control" id="vessel_registration_number" placeholder="" v-model="vessel.registration_number" required=""/>
                </div>
            </div>
            <div class="form-group">
                <label for="" class="col-sm-3 control-label">Vessel name</label>
                <div class="col-sm-9">
                    <input type="text" class="form-control" id="vessel_name" placeholder="" v-model="vessel.name" required=""/>
                </div>
            </div>
            <div class="form-group">
                <label for="" class="col-sm-3 control-label">Registration vessel owner</label>
                <div class="col-sm-9">
                    <input type="radio" name="registered_owner_current_user" value="current_user" v-model="vessel.registered_owner" required="">
                    Current User
                    </input>
                </div>
                <div class="col-sm-2">
                    <input type="radio" id="registered_owner_company" name="registered_owner_company" value="company_name" v-model="vessel.registered_owner" required="">
                    Your company
                    </input>
                </div>
                <div class="col-sm-6">
                    <input type="text" class="form-control" id="registered_owner_company_name" placeholder="" v-model="vessel.registered_owner_company_name" required=""/>
                </div>
            </div>
            <div class="form-group">
                <label for="" class="col-sm-3 control-label">Ownership percentage</label>
                <div class="col-sm-9">
                    <input type="text" class="form-control" id="ownership_percentage" placeholder="" v-model="vessel.ownership_percentage" required=""/>
                </div>
            </div>
            <div class="form-group">
                <label for="" class="col-sm-3 control-label">Permanent or usual place of berthing/mooring of vessel</label>
                <div class="col-sm-9">
                    <input type="text" class="form-control" id="berth_mooring" placeholder="" v-model="vessel.berth_mooring" required=""/>
                </div>
            </div>
            <div class="form-group">
                <label for="" class="col-sm-3 control-label">Copy of DoT registration papers</label>
            </div>
        </FormSection>
        <FormSection label="Vessel Details">
            <div class="form-group">
                <label for="" class="col-sm-3 control-label">Vessel length</label>
                <div class="col-sm-9">
                    <input type="text" class="form-control" id="vessel_length" placeholder="" v-model="vessel.vessel_length" required=""/>
                </div>
            </div>
            <div class="form-group">
                <label for="" class="col-sm-3 control-label">Overall length of vessel</label>
                <div class="col-sm-9">
                    <input type="text" class="form-control" id="overall_length" placeholder="" v-model="vessel.overall_length" required=""/>
                </div>
            </div>
            <div class="form-group">
                <label for="" class="col-sm-3 control-label">Displacement tonnage</label>
                <div class="col-sm-9">
                    <input type="text" class="form-control" id="displacement_tonnage" placeholder="" v-model="vessel.displacement_tonnage" required=""/>
                </div>
            </div>
            <div class="form-group">
                <label for="" class="col-sm-3 control-label">Draft</label>
                <div class="col-sm-9">
                    <input type="text" class="form-control" id="draft" placeholder="" v-model="vessel.draft" required=""/>
                </div>
            </div>
            <div class="form-group">
                <label for="" class="col-sm-3 control-label">Vessel Type</label>
                <div class="col-sm-9">
                    <select class="form-control" style="width:50%" v-model="vessel.vessel_type">
                        <option v-for="vesselType in vesselTypes" :value="vesselType.code">
                            {{ vesselType.description }}
                        </option>
                    </select>
                </div>
            </div>
        </FormSection>
    </div>
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
                vessel: {},
                vesselTypes: [],
            }
        },
        components:{
            FormSection,
        },
        props:{
            proposal:{
                type: Object,
                required:true
            }
        },
        computed: {
            fee_invoice_url: function(){
                return this.fee_paid ? this.proposal.fee_invoice_url : '';
            }
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
        },
        mounted:function () {
        },
        created: function() {
            this.fetchVesselTypes();
        },
    }
</script>

<style lang="css" scoped>
</style>

