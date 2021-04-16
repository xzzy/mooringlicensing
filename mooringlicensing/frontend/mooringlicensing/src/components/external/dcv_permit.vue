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
                <label for="" class="col-sm-3 control-label">UIV vessel identifier</label>
                <div class="col-sm-6">
                    <input type="text" class="form-control" name="uiv_vessel_identifier" placeholder="" v-model="dcv_permit.uiv_vessel_identifier">
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
                uiv_vessel_identifier: '',
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
        submit_and_pay: function(){
            // submit_and_pay() --> save_and_pay() --> post_and_redirect()
            let vm = this
            vm.paySubmitting = true;

            swal({
                title: "DCV Permit Application",
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
                const res = await this.save(false, '/api/dcv_permit/')
                this.dcv_permit.id = res.body.id
                await this.post_and_redirect(this.dcv_permit_fee_url, {'csrfmiddlewaretoken' : this.csrf_token});
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
        post_and_redirect: function(url, postData) {
            /* http.post and ajax do not allow redirect from Django View (post method), 
               this function allows redirect by mimicking a form submit.

               usage:  vm.post_and_redirect(vm.application_fee_url, {'csrfmiddlewaretoken' : vm.csrf_token});
            */
            var postFormStr = "<form method='POST' action='" + url + "'>";

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
