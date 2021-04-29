<template lang="html">
    <div class="container" >
        <Vessel
        :profile=profile
        id="managevessel" 
        ref="managevessel"
        :readonly=false
        />
        <div>
            <input type="hidden" name="csrfmiddlewaretoken" :value="csrf_token"/>

            <div class="row" style="margin-bottom: 50px">
                    <div  class="container">
                      <div class="row" style="margin-bottom: 50px">
                          <div class="navbar navbar-fixed-bottom"  style="background-color: #f5f5f5;">
                              <div class="navbar-inner">
                                <div class="container">
                                  <p class="pull-right" style="margin-top:5px">
                                    <button v-if="savingVessel" type="button" class="btn btn-primary" disabled>Save and Exit&nbsp;
                                            <i class="fa fa-circle-o-notch fa-spin fa-fw"></i></button>
                                    <input v-else type="button" @click.prevent="save_exit" class="btn btn-primary" value="Save and Exit" :disabled="savingVessel"/>
                                    <button v-if="savingVessel" type="button" class="btn btn-primary" disabled>Save and Continue&nbsp;
                                            <i class="fa fa-circle-o-notch fa-spin fa-fw"></i></button>
                                    <input v-else type="button" @click.prevent="save" class="btn btn-primary" value="Save and Continue" :disabled="savingVessel"/>

                                    <router-link class="btn btn-primary" :to="{name: 'vessels-dashboard'}">Back to Dashboard</router-link>
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
import WaitingListApplication from '../form_wla.vue';
import AnnualAdmissionApplication from '../form_aaa.vue';
import AuthorisedUserApplication from '../form_aua.vue';
import MooringLicenceApplication from '../form_mla.vue';
import Vessel from '../common/vessels.vue';
import Vue from 'vue' 
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
export default {
  name: 'ManageVessel',
  data: function() {
    return {
        profile: {},
        savingVessel: false,
    }
  },
  components: {
      Vessel,
  },
  computed: {
      csrf_token: function() {
        return helpers.getCookie('csrftoken')
      },
  },
  methods: {
    populateProfile: async function() {
        const response = await this.$http.get(api_endpoints.profile);
        this.profile = Object.assign({}, response.body);
    },
    save: async function(withConfirm=true, url=this.proposal_form_url) {
        let vm = this;
        vm.savingProposal=true;
        vm.save_applicant_data();

        //let formData = vm.set_formData()
        //vm.$http.post(vm.proposal_form_url,formData).then(res=>{
        let payload = {
            proposal: {},
            vessel: {},
        }

        //vm.$http.post(vm.proposal_form_url,payload).then(res=>{
        const res = await vm.$http.post(url, payload);
        if (res.ok) {
            if (withConfirm) {
                swal(
                    'Saved',
                    'Your application has been saved',
                    'success'
                );
            };
            vm.savingProposal=false;
            return res;
        } else {
            swal({
                title: "Please fix following errors before saving",
                text: err.bodyText,
                type:'error'
            });
            vm.savingProposal=false;
        }
    },
    save_exit: function() {
      let vm = this;
      this.submitting = true;
      this.saveExitProposal=true;
      this.save();
      this.saveExitProposal=false;
      // redirect back to dashboard
      vm.$router.push({
        name: 'external-dashboard'
      });
    },

    save_wo_confirm: function() {
      this.save(false);
        /*
      let vm = this;
      vm.save_applicant_data();
      let formData = vm.set_formData()

      vm.$http.post(vm.proposal_form_url,formData);
      */
    },

    leaving: function(e) {
      let vm = this;
      var dialogText = 'You have some unsaved changes.';
      if (!vm.proposal_readonly && !vm.submitting){
        e.returnValue = dialogText;
        return dialogText;
      }
      else{
        return null;
      }
    },
    

  },

  mounted: function() {
    let vm = this;
    this.populateProfile();
    //vm.form = document.forms.new_proposal;
      /* uncomment later - too annoying while making front end changes 
    window.addEventListener('beforeunload', vm.leaving);
    window.addEventListener('onblur', vm.leaving);
    */
  },
}
</script>

<style lang="css" scoped>
</style>
