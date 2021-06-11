<template lang="html">
    <div class="container" >
        <!--button type="button" @click="createML">Mooring Licence Application</button-->
        <div class="row">
            <div class="col-sm-12">
                <form class="form-horizontal" name="personal_form" method="post">
                    <FormSection label="Apply for">
                        <div>
                            <div class="col-sm-12" style="margin-left:20px">
                                <div class="form-group">
                                    <label>Do you want to apply</label>
                                    <div v-for="application_type in application_types">
                                        <input 
                                        type="radio" 
                                        name="applicationType" 
                                        :id="application_type.code" 
                                        value="application_type" 
                                        @change="selectApplication(application_type)"
                                        />
                                        <label :for="application_type.code" style="font-weight:normal">{{ application_type.new_application_text }}</label>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </FormSection>

                    <!--div class="col-sm-12" v-show="has_active_proposals()">
                        <p style="color:red;"> An active application already exists in the system: </p>
                        <p style="color:red;"> {{ active_proposals() }}</p>
                    </div-->
                    <div class="col-sm-12">
                        <button v-if="!creatingProposal" :disabled="isDisabled" @click.prevent="submit()" class="btn btn-primary pull-right">Continue</button>
                        <button v-else disabled class="pull-right btn btn-primary"><i class="fa fa-spin fa-spinner"></i>&nbsp;Creating</button>
                    </div>
                  </form>
            </div>
        </div>
    </div>
</template>
<script>
import Vue from 'vue'
import FormSection from '@/components/forms/section_toggle.vue'
//require('bootstrap/dist/css/bootstrap.css')
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
import utils from './utils'
export default {
  data: function() {
    let vm = this;
    return {
        "proposal": null,
        profile: {
        },
        "loading": [],
        form: null,
        selectedApplication: {},
        //selected_application_name: '',
        application_types: [],
        creatingProposal: false,
        //site_url: (api_endpoints.site_url.endsWith("/")) ? (api_endpoints.site_url): (api_endpoints.site_url + "/"),
    }
  },
  components: {
      FormSection
  },
  computed: {
    isLoading: function() {
      return this.loading.length > 0
    },
    isDisabled: function() {
        /*
        let vm = this;
        if ((vm.org_applicant == '' && vm.yourself=='') ||( vm.selected_application_id == '')){
                return true;
            }
            */
        let disabled = true;
        if (this.selectedApplication && this.selectedApplication.code) {
            disabled = false;
        }
        return disabled;
    },
    alertText: function() {
        let text = '';
        if (this.selectedApplication && this.selectedApplication.description) {
            text = this.selectedApplication.description;
        }
		if (this.selectedApplication.code == 'wla') {
            text = "a " + text;
		} else {
        	//return "a Filming";
            text = "an "+ text;
        }
        return text
	},

  },
  methods: {
    selectApplication(applicationType) {
        this.selectedApplication = Object.assign({}, applicationType)
    },
    submit: function() {
        //let vm = this;
        swal({
            title: "Create " + this.selectedApplication.description,
            text: "Are you sure you want to create " + this.alertText + "?",
            type: "question",
            showCancelButton: true,
            confirmButtonText: 'Accept'
        }).then(() => {
            this.createProposal();
            /*
            if (!vm.has_active_proposals()) {
         	    vm.createProposal();
            }
            */
        },(error) => {
        });
    },
      /*
    createML: async function() {
        const res = await this.$http.post(api_endpoints.mooringlicenceapplication);
        const proposal = res.body;
		this.$router.push({
			name:"draft_proposal",
			params:{proposal_id:proposal.id}
		});
        this.creatingProposal = false;
    },
    */
    createProposal: async function () {
        this.creatingProposal = true;
        let payload = {
        }
        let res = null;
        if (this.selectedApplication && this.selectedApplication.code === 'wla') {
            res = await this.$http.post(api_endpoints.waitinglistapplication, payload);
        } else if (this.selectedApplication && this.selectedApplication.code === 'aaa') {
            res = await this.$http.post(api_endpoints.annualadmissionapplication, payload);
        } else if (this.selectedApplication && this.selectedApplication.code === 'aua') {
            res = await this.$http.post(api_endpoints.authoriseduserapplication, payload);
        } else if (this.selectedApplication && this.selectedApplication.app_type_code === 'ml') {
            payload.mooring_id = this.selectedApplication.mooring_id;
            payload.approval_id = this.selectedApplication.approval_id;
            res = await this.$http.post(api_endpoints.mooringlicenceapplication, payload);
        } 
        const proposal = res.body;
		this.$router.push({
			name:"draft_proposal",
			params:{proposal_id:proposal.id}
		});
        this.creatingProposal = false;
    },
	searchList: function(id, search_list){
        /* Searches for dictionary in list */
        for (var i = 0; i < search_list.length; i++) {
            if (search_list[i].value == id) {
                return search_list[i];
            }
        }
        return [];
    },
    fetchApplicationTypes: async function(){
        const response = await this.$http.get(api_endpoints.application_types_dict+'?apply_page=True');
        for (let app_type of response.body) {
            this.application_types.push(app_type)
        }
    },
    fetchExistingMooringLicences: async function(){
        /*
        let payload = {
            'submitter': profile,
        }
        */
        const response = await this.$http.get(api_endpoints.existing_mooring_licences);
        //console.log(response.body)
        for (let ml of response.body) {
            this.application_types.push(ml)
        }
    },

  },
  mounted: async function() {
    //let vm = this;
    await this.fetchApplicationTypes();
    await this.fetchExistingMooringLicences();
    this.form = document.forms.new_proposal;
  },
  beforeRouteEnter: function(to, from, next) {

    let initialisers = [
        utils.fetchProfile(),
        
        //utils.fetchProposal(to.params.proposal_id)
    ]
    next(vm => {
        vm.loading.push('fetching profile')
        Promise.all(initialisers).then(data => {
            vm.profile = data[0];
            //vm.proposal = data[1];
            vm.loading.splice('fetching profile', 1)
        })
    })
    
  }
}
</script>

<style lang="css">
input[type=text], select{
    width:40%;
    box-sizing:border-box;

    min-height: 34px;
    padding: 0;
    height: auto;
}

.group-box {
	border-style: solid;
	border-width: thin;
	border-color: #FFFFFF;
}
.radio-buttons {
    padding: 5px;
}
</style>
