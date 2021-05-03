<template>
    <div class="container" id="externalDash">
        <FormSection :formCollapse="false" label="DCV Admission Fees" Index="dcv_admission">
            <div class="row mb-2">
                <div class="col-sm-12">
                    <strong>Collection and remittance of admission fees is required prior to entering the Rottnest Island Reserve.  Penalties do apply for non compliance.</strong>
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">UIV Vessel Identifier</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="uvi_vessel_identifier" placeholder="" v-model="dcv_admission.dcv_vessel.uvi_vessel_identifier">
                </div>
            </div>
            <div class="row form-group">
                <label for="vessel_search" class="col-sm-3 control-label">Vessel registration number</label>
                <div class="col-sm-9">
                    <select :disabled="readonly" id="vessel_search" name="vessel_registration" ref="dcv_vessel_rego_nos" class="form-control" style="width: 40%">
                    </select>
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Vessel name</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="vessel_name" placeholder="" v-model="dcv_admission.dcv_vessel.vessel_name">
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Skipper</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="skipper" placeholder="" v-model="dcv_admission.skipper">
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Contact number</label>
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
                    :dcv_vessel="dcv_admission.dcv_vessel"
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
                                        <button v-if="paySubmitting" type="button" class="btn btn-primary" disabled>Pay and Submit&nbsp;<i class="fa fa-circle-o-notch fa-spin fa-fw"></i></button>
                                        <input v-else type="button" @click.prevent="pay_and_submit" class="btn btn-primary" value="Pay and Submit" :disabled="paySubmitting"/>
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

var select2 = require('select2');
require("select2/dist/css/select2.min.css");
require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");
  
export default {
    name: 'DcvAdmissionPage',
    props: {
        level: {
            type: String,
            default: 'external',
        },
        readonly:{
            type: Boolean,
            default: false,
        },
    },
    data() {
        let vm = this;
        return {
            dcv_admission: {
                id: null,
                dcv_vessel: {
                    id: null,
                    uvi_vessel_identifier: '',
                    rego_no: '',
                    vessel_name: '',
                },
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
                annual_admission_permit: [],
                authorised_user_permit: [],
                mooring_licence: [],
                dcv_permit: [],
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
        lookupDcvVessel: async function(id) {
            console.log('in lookupDcvVessel')
            const res = await this.$http.get(api_endpoints.lookupDcvVessel(id));
            const vesselData = res.body;
            console.log('existing dcv_vessel: ')
            console.log(vesselData);
            if (vesselData && vesselData.rego_no) {
                this.dcv_admission.dcv_vessel = Object.assign({}, vesselData);
            }
        },
        initialiseSelects: function(){
            let vm = this;
            $(vm.$refs.dcv_vessel_rego_nos).select2({
                minimumInputLength: 2,
                "theme": "bootstrap",
                allowClear: true,
                placeholder:"Select Vessel Registration",
                tags: true,
                createTag: function (tag) {
                    console.log('in createTag')
                    console.log('tag: ')
                    console.log(tag)
                    return {
                        id: tag.term,
                        text: tag.term,
                        isNew: true,
                    };
                },
                ajax: {
                    url: api_endpoints.dcv_vessel_rego_nos,
                    dataType: 'json',
                }
            }).
            on("select2:select",function (e) {
                console.log('select2:select')
                console.log('e: ')
                console.log(e)
                var selected = $(e.currentTarget);
                console.log('selected: ')
                console.log(selected)
                //vm.vessel.rego_no = selected.val();
                const id = selected.val();
                console.log('val(): ')
                console.log(id)
                vm.$nextTick(() => {
                    //if (!isNew) {
                    if (e.params.data.isNew) {
                        // fetch the selected vessel from the backend
                        console.log("new");
                        vm.dcv_admission.dcv_vessel.rego_no = id
                        //vm.dcv_admission.dcv_vessel = Object.assign({}, 
                        //    {
                        //        rego_no: id,
                        //    });
                    } else {
                        // fetch the selected vessel from the backend
                        console.log('existing')
                        vm.lookupDcvVessel(id);
                    }
                });
            }).
            on("select2:unselect",function (e) {
                console.log('select2:unselect')
                var selected = $(e.currentTarget);
                //vm.dcv_admission.dcv_vessel.rego_no = '';
                vm.dcv_admission.dcv_vessel = Object.assign({}, 
                    {
                        id: null,
                        uvi_vessel_identifier: '',
                        rego_no: '',
                        vessel_name: '',
                    }
                );

                //vm.selectedRego = ''
            }).
            on("select2:open",function (e) {
                console.log('select2:open')
                //document.getElementsByClassName("select2-search__field")[0].focus();
                console.log($(".select2-search__field"));
                $(".select2-search__field")[0].focus();
            });
            // read vessel.rego_no if exists on vessel.vue open
            //vm.readRegoNo();
        },
        pay_and_submit: function(){
            // pay_and_submit() --> save_and_pay() --> post_and_redirect()
            let vm = this
            vm.paySubmitting = true;

            swal({
                title: "DCV Admission",
                text: "Are you sure you want to pay and submit for this application?",
                type: "question",
                showCancelButton: true,
                confirmButtonText: "Pay and Submit",
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
                console.log('res: ')
                console.log(res)
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
            this.initialiseSelects()
            this.addEventListeners()
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
