<template>
    <div class="container" id="externalDash">
        <FormSection :formCollapse="false" label="DCV Admission Fees" Index="dcv_admission_fees">
            <div class="row mb-2">
                <div class="col-sm-12">
                    <strong>Collection and remittance of admission fees is required prior to entering the Rottnest Island Reserve.  Penalties do apply for non compliance.</strong>
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-2 control-label">UIV Vessel Identifier</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="uvi_vessel_identifier" placeholder="" v-model="dcv_admission_fees.uvi_vessel_identifier">
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-2 control-label">Vessel registration</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="vessel_registration" placeholder="" v-model="dcv_admission_fees.vessel_registration">
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-2 control-label">Vessel name</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="vessel_name" placeholder="" v-model="dcv_admission_fees.vessel_name">
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-2 control-label">Skipper</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="skipper" placeholder="" v-model="dcv_admission_fees.skipper">
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-2 control-label">Contact number</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="contact_number" placeholder="" v-model="dcv_admission_fees.contact_number">
                </div>
            </div>
        </FormSection>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue'
import FormSection from "@/components/forms/section_toggle.vue"
import { api_endpoints, helpers } from '@/utils/hooks'

export default {
    name: 'DcvTablePage',
    data() {
        let vm = this;
        return {
            dcv_admission_fees: {
                id: null,
                uvi_vessel_identifier: '',
                vessel_registration: '',
                vessel_name: '',
                skipper: '',
                contact_number: '',
            },
        }
    },
    components:{
        FormSection,
    },
    watch: {

    },
    computed: {
        is_external: function() {
            return this.level == 'external'
        },

    },
    methods: {

    },
    mounted: function () {

    },
    created: function() {

    },
}
</script>

<style>
.mb-1 {
    margin: 0 0 1em 0;
}
.mb-2 {
    margin: 0 0 2em 0;
}
</style>
