<template>
    <div class="container" id="externalDash">
        <FormSection :formCollapse="false" label="DCV Permit" Index="dcv_permit">
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Organisation</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="organisation" placeholder="" v-model="dcv_permit.organisation">
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">ABN / ACN</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="abn_acn" placeholder="" v-model="dcv_permit.abn_acn">
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Year</label>
                <div class="col-sm-6">
                    <select class="form-control" v-model="dcv_permit.season">
                        <option value=""></option>
                        <option v-for="season in season_options" :value="season">{{ season.name }}</option>
                    </select>
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">UVI vessel identifier</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="uvi_vessel_identifier" placeholder="" v-model="dcv_permit.uvi_vessel_identifier">
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Vessel registration number</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="rego_no" placeholder="" v-model="dcv_permit.rego_no">
                </div>
            </div>
            <div class="row form-group">
                <label for="" class="col-sm-3 control-label">Vessel name</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="vessel_name" placeholder="" v-model="dcv_permit.vessel_name">
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
import datatable from '@/utils/vue/datatable.vue'
import FormSection from "@/components/forms/section_toggle.vue"
import { api_endpoints, helpers } from '@/utils/hooks'

export default {
    name: 'DcvTablePage',
    data() {
        let vm = this;
        return {
            dcv_permit: {
                id: null,
                organisation: '',
                abn_acn: '',
                season: null,
                uvi_vessel_identifier: '',
                rego_no: '',
                vessel_name: '',
            },
            paySubmitting: false,
            season_options: [],
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
        dcv_permit_fee_url: function() {
          return `/dcv_permit_fee/${this.dcv_permit.id}/`
        },
    },
    methods: {
        pay_and_submit: function(){
            // pay_and_submit() --> save_and_pay() --> post_and_redirect()
            let vm = this
            vm.paySubmitting = true;

            swal({
                title: "DCV Permit Application",
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
                const res = await this.save(false, '/api/dcv_permit/')
                this.dcv_permit.id = res.body.id
                await helpers.post_and_redirect(this.dcv_permit_fee_url, {'csrfmiddlewaretoken' : this.csrf_token});
            } catch(err) {
                helpers.processError(err)
            }
        },
        save: async function(withConfirm=true, url){
            try{
                const res = await this.$http.post(url, this.dcv_permit)
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
        fetchFilterLists: function(){
            let vm = this;

            // Seasons
            vm.$http.get(api_endpoints.seasons_for_dcv_dict + '?apply_page=False').then((response) => {
                vm.season_options = response.body
            },(error) => {
                console.log(error);
            })
        },
    },
    mounted: function () {

    },
    created: function() {
        this.fetchFilterLists()
    },
}
</script>
