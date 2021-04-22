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

            <div class="panel panel-default">
                <div class="panel-body">
                    <div class="row form-group">
                        <label for="" class="col-sm-2 control-label">Arrival</label>
                        <div class="col-sm-3 input-group date" ref="arrivalDatePicker">
                            <input type="text" class="form-control" placeholder="DD/MM/YYYY" id="period_from_input_element"/>
                            <span class="input-group-addon">
                                <span class="glyphicon glyphicon-calendar"></span>
                            </span>
                        </div>
                    </div>
                    <div class="row form-group">
                        <label for="" class="col-sm-2 control-label">Private visit</label>
                        <div class="col-sm-2">
                            <input type="radio" id="private_yes" name="private_visit" value="true" v-model="dcv_admission_fees.private_visit"/>
                            <label class="radio-inline control-label" for="private_yes">Yes</label>
                        </div>
                        <div class="col-sm-2">
                            <input type="radio" id="private_no" name="private_visit" value="false" v-model="dcv_admission_fees.private_visit"/>
                            <label class="radio-inline control-label" for="private_no">No</label>
                        </div>
                    </div>
                    <div class="row form-group">
                        <div class="col-sm-2"></div>
                        <div class="col-sm-2 text-center"><label>Landing</label></div>
                        <div class="col-sm-2 text-center"><label>Extended stay</label></div>
                        <div class="col-sm-2 text-center"><label>Not landing</label></div>
                        <div class="col-sm-2 text-center"><label>Approved events</label></div>
                    </div>
                    <div class="row form-group">
                        <div class="col-sm-2"><label>Number of Adults</label><br />(12 and over)</div>
                        <div class="col-sm-2">
                            <input type="number" min="0" max="100" step="1" class="form-control" name="adults-landing" placeholder="" v-model="dcv_admission_fees.adults_landing">
                        </div>
                        <div class="col-sm-2">
                            <input type="number" min="0" max="100" step="1" class="form-control" name="adults-extended-stay" placeholder="" v-model="dcv_admission_fees.adults_extended_stay">
                        </div>
                        <div class="col-sm-2">
                            <input type="number" min="0" max="100" step="1" class="form-control" name="adults-not-landing" placeholder="" v-model="dcv_admission_fees.adults_not_landing">
                        </div>
                        <div class="col-sm-2">
                            <input type="number" min="0" max="100" step="1" class="form-control" name="adults-approved-events" placeholder="" v-model="dcv_admission_fees.adults_approved_events">
                        </div>
                    </div>
                    <div class="row form-group">
                        <div class="col-sm-2"><label>Number of Children</label><br />(4 - 12)</div>
                        <div class="col-sm-2">
                            <input type="number" min="0" max="100" step="1" class="form-control" name="children-landing" placeholder="" v-model="dcv_admission_fees.children_landing">
                        </div>
                        <div class="col-sm-2">
                            <input type="number" min="0" max="100" step="1" class="form-control" name="children-extended-stay" placeholder="" v-model="dcv_admission_fees.children_extended_stay">
                        </div>
                        <div class="col-sm-2">
                            <input type="number" min="0" max="100" step="1" class="form-control" name="children-not-landing" placeholder="" v-model="dcv_admission_fees.children_not_landing">
                        </div>
                        <div class="col-sm-2">
                            <input type="number" min="0" max="100" step="1" class="form-control" name="children-approved-events" placeholder="" v-model="dcv_admission_fees.children_approved_events">
                        </div>
                    </div>
                </div>
            </div>
        </FormSection>

        <div>
            <input type="hidden" name="csrfmiddlewaretoken" :value="csrf_token"/>

            <div class="row" style="margin-bottom: 50px">
                <div  class="container">
                    <div class="row" style="margin-bottom: 50px">
                        <div class="navbar navbar-fixed-bottom"  style="background-color: #f5f5f5;">
                            <div class="navbar-inner">
                                <div class="container">
                                    <p class="pull-right" style="margin-top:5px">
                                        <button v-if="paySubmitting" type="button" class="btn btn-primary" disabled>Submit and Pay&nbsp;<i class="fa fa-circle-o-notch fa-spin fa-fw"></i></button>
                                        <input v-else type="button" @click.prevent="submit_and_pay" class="btn btn-primary" value="Submit and Pay" :disabled="paySubmitting"/>
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import 'eonasdan-bootstrap-datetimepicker';
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
                arrival: null,
            },
            paySubmitting: false,
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
        csrf_token: function() {
          return helpers.getCookie('csrftoken')
        },
    },
    methods: {
        addEventListeners: function () {
            let vm = this;
            let el_fr = $(vm.$refs.arrivalDatePicker);
            let options = {
                format: "DD/MM/YYYY",
                showClear: true ,
                useCurrent: false,
            };

            el_fr.datetimepicker(options);

            el_fr.on("dp.change", function(e) {
                let selected_date = null;
                if (e.date){
                    // Date selected
                    selected_date = e.date.format('DD/MM/YYYY')  // e.date is moment object
                    vm.on_site_information.period_from = selected_date;
                } else {
                    // Date not selected
                    vm.on_site_information.period_from = selected_date;
                }
            });
        },
    },
    mounted: function () {
        this.$nextTick(() => {
            this.addEventListeners();
        });
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
