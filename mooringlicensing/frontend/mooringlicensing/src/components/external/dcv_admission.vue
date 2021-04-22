<template>
    <div class="container" id="externalDash">
        <FormSection :formCollapse="false" label="DCV Admission Fees" Index="dcv_admission">
            <div class="row mb-2">
                <div class="col-sm-12">
                    <strong>Collection and remittance of admission fees is required prior to entering the Rottnest Island Reserve.  Penalties do apply for non compliance.</strong>
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-2 control-label">UIV Vessel Identifier</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="uvi_vessel_identifier" placeholder="" v-model="dcv_admission.uvi_vessel_identifier">
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-2 control-label">Vessel registration</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="vessel_registration" placeholder="" v-model="dcv_admission.vessel_registration">
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-2 control-label">Vessel name</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="vessel_name" placeholder="" v-model="dcv_admission.vessel_name">
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-2 control-label">Skipper</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="skipper" placeholder="" v-model="dcv_admission.skipper">
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-2 control-label">Contact number</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="contact_number" placeholder="" v-model="dcv_admission.contact_number">
                </div>
            </div>

            <template class="" id="arrival_panels" v-for="arrival in dcv_admission.arrivals">
                <PanelArrival
                    level="external"
                    :uuid="arrival.uuid"
                    :arrival="arrival"
                    @delete_arrival="delete_arrival"
                    :key="arrival.uuid"
                />
            </template>

            <div class="row">
                <div class="col-sm-12">
                    <div class="pull-right">
                        <label>Click <span @click="add_another_date_clicked" class="add_another_date_text">here</span> to add another date</label>
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
import PanelArrival from "@/components/common/panel_dcv_admission_arrival.vue"
import { api_endpoints, helpers } from '@/utils/hooks'
import uuid from 'uuid'
  
export default {
    name: 'DcvAdmissionPage',
    props: {
        level: {
            type: String,
            default: 'external',
        }
    },
    data() {
        let vm = this;
        return {
            dcv_admission: {
                id: null,
                uvi_vessel_identifier: '',
                vessel_registration: '',
                vessel_name: '',
                skipper: '',
                contact_number: '',
                arrivals: [
                    {
                        uuid: uuid(),
                        arrival_date: null,
                        private_visit: null,
                        adults: {
                            landing: 0,
                            extended_stay: 0,
                            not_landing: 0,
                            approved_events: 0,
                        },
                        children: {
                            landing: 0,
                            extended_stay: 0,
                            not_landing: 0,
                            approved_events: 0,
                        }
                    },
                ],
            },
            paySubmitting: false,
        }
    },
    components:{
        PanelArrival,
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
        dcv_admission_fee_url: function() {
          return `/dcv_admission_fee/${this.dcv_admission.id}/`
        },
    },
    methods: {
        submit_and_pay: function(){
            // submit_and_pay() --> save_and_pay() --> post_and_redirect()
            let vm = this
            vm.paySubmitting = true;

            swal({
                title: "DCV Admission",
                text: "Are you sure you want to submit and pay for this application?",
                type: "question",
                showCancelButton: true,
                confirmButtonText: "Submit and Pay",
            }).then(
                (res)=>{
                    vm.save_and_pay();
                    this.paySubmitting = false
                },
                (res)=>{
                    this.paySubmitting = false
                },
            )
        },
        save_and_pay: async function() {
            try{
                const res = await this.save(false, '/api/dcv_admission/')
                this.dcv_admission.id = res.body.id
                await helpers.post_and_redirect(this.dcv_admission_fee_url, {'csrfmiddlewaretoken' : this.csrf_token});
            } catch(err) {
                helpers.processError(err)
            }
        },
        save: async function(withConfirm=true, url){
            try{
                const res = await this.$http.post(url, this.dcv_admission)
                if (withConfirm) {
                    swal(
                        'Saved',
                        'Your application has been saved',
                        'success'
                    );
                };
                return res;
            } catch(err){
                helpers.processError(err)
            }
        },
        delete_arrival: function(uuid){
            for (let i=0; i < this.dcv_admission.arrivals.length; i++){
                if (this.dcv_admission.arrivals[i].uuid === uuid){
                    this.dcv_admission.arrivals.splice(i, 1)
                    break
                }
            }
        },
        add_another_date_clicked: function() {
            this.dcv_admission.arrivals.push(
                {
                    uuid: uuid(),
                    arrival_date: null,
                    private_visit: null,
                    adults: {
                        landing: 0,
                        extended_stay: 0,
                        not_landing: 0,
                        approved_events: 0,
                    },
                    children: {
                        landing: 0,
                        extended_stay: 0,
                        not_landing: 0,
                        approved_events: 0,
                    }
                }
            )
        },
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
.add_another_date_text {
    cursor: pointer;
    color: #337ab7;
}
</style>
