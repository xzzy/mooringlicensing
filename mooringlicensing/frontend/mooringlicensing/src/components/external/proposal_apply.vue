<template lang="html">
    <div class="container" >
        <div class="row">
            <div class="col-sm-12">
                <form class="form-horizontal" name="personal_form" method="post">
                    <!-- should probably use FormSection here instead-->
                    <!--div class="panel panel-default">
                        <div class="panel-heading">
                            <h3 class="panel-title">Applicant <small>The applicant will be the licensee.</small><i class="fa fa-question-circle" data-toggle="tooltip" data-placement="bottom" style="color:blue" title="Please ensure the applicant is the same as the insured party on your public liability on your public liability insurance certificate.">&nbsp;</i>
                                <a :href="'#'+pBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="pBody">
                                    <span class="glyphicon glyphicon-chevron-up pull-right "></span>
                                </a>
                            </h3>
                        </div>
                        <div class="panel-body collapse in" :id="pBody">

                            <div class="col-sm-12">
                                <div class="form-group" v-if="!isLoading">
                                    <div v-if="profile.mooringlicensing_organisations.length > 0">
                                        <label>Do you apply </label> </br>
                                        <div v-for="org in profile.mooringlicensing_organisations" class="radio">
                                            <label v-if ="!org.is_consultant">
                                              <input type="radio" name="behalf_of_org" v-model="org_applicant"  :value="org.id"> On behalf of {{org.name}}
                                            </label>
                                            <label v-if ="org.is_consultant">
                                              <input type="radio" name="behalf_of_org" v-model="org_applicant"  :value="org.id"> On behalf of {{org.name}} (as a Consultant)
                                            </label>
                                        </div>
                                    </div>
                                    <div v-else>
                                        <p style="color:red"> You cannot start a new application as you have not linked yourself to any organisation yet. Please go to your account page in the Options menu to link yourself to an organisation.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div-->

                    <!--div v-if="org_applicant != ''||yourself!=''" class="panel panel-default"-->
                    <FormSection label="Apply for">
                        <div>
                            <label for="" class="control-label" >Licence Type * <a :href="proposal_type_help_url" target="_blank"><i class="fa fa-question-circle" style="color:blue">&nbsp;</i></a></label>
                            <div class="col-sm-12">
                                <div class="form-group">
                                    <select class="form-control" style="width:40%" v-model="selected_application_id" @change="chainedSelectAppType(selected_application_id)">
                                        <option value="" selected disabled>Select Licence type*</option>
                                        <option v-for="application_type in application_types" :value="application_type">
                                            {{ application_type }}
                                        </option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </FormSection>

                    <!--div class="col-sm-12" v-show="has_active_proposals()">
                        <p style="color:red;"> An active application already exists in the system: </p>
                        <p style="color:red;"> {{ active_proposals() }}</p>
                    </div-->
                    <div class="col-sm-12">
                        <button v-if="!creatingProposal" :disabled="isDisabled() || has_active_proposals()" @click.prevent="submit()" class="btn btn-primary pull-right">Continue</button>
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
        agent: {},
        behalf_of: '',
        org_applicant: '',
        yourself: '',
        profile: {
            mooringlicensing_organisations: []
        },
        "loading": [],
        form: null,
        pBody: 'pBody' + vm._uid,
        pBody2: 'pBody2' + vm._uid,

        selected_application_id: '',
        selected_application_name: '',
        application_types: [],
        categories: [],
        approval_level: '',
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
    org: function() {
        let vm = this;
        if (vm.org_applicant != '' && vm.org_applicant != 'yourself'){   
            return vm.profile.mooringlicensing_organisations.find(org => parseInt(org.id) === parseInt(vm.org_applicant)).name;
        }
        return vm.org_applicant;
    },
    proposal_type_help_url: function() {
      return api_endpoints.proposal_type_help_url;
    },

  },
  methods: {
    has_active_proposals: function() {
        return this.active_proposals().length > 0;
    },
    active_proposals: function() {
        // returns active 'T Class' proposals - cannot have more than 1 active 'T Class' application at a time
        let vm = this;
        var proposals = [];
        var org = vm.profile.mooringlicensing_organisations.find(el => el.name === vm.org)
        if (org && vm.selected_application_name == vm.application_type_tclass) {
            proposals = org.active_proposals.find(el => el.application_type === vm.application_type_tclass).proposals
        }
        return proposals;
    },
    submit: function() {
        let vm = this;
		console.log(vm.org_applicant)
        swal({
            title: "Create " + vm.selected_application_name,
            text: "Are you sure you want to create " + this.alertText() + " application on behalf of "+vm.org+" ?",
            type: "question",
            showCancelButton: true,
            confirmButtonText: 'Accept'
        }).then(() => {
            if (!vm.has_active_proposals()) {
         	    vm.createProposal();
            }
        },(error) => {
        });
    },
    alertText: function() {
        let vm = this;
		if (vm.selected_application_name == vm.application_type_tclass) {
        	//return "a T Class";
            return "a "+vm.application_type_tclass;
		} else if (vm.selected_application_name == vm.application_type_filming) {
        	//return "a Filming";
            return "a "+vm.application_type_filming;
		} else if (vm.selected_application_name == vm.application_type_event) {
        	//return "an Event";
            return "an "+vm.application_type_event;
		}
	},
    createProposal:function () {
        let vm = this;
        vm.creatingProposal = true;
        if(vm.org_applicant=='yourself'){
            vm.org_applicant='';
        }
		vm.$http.post('/api/proposal.json',{
			//behalf_of: vm.behalf_of,
            org_applicant:vm.org_applicant,
			application: vm.selected_application_id,
			region: vm.selected_region,
			district: vm.selected_district,
			//tenure: vm.selected_tenure,
			activity: vm.selected_activity,
            sub_activity1: vm.selected_sub_activity1,
            sub_activity2: vm.selected_sub_activity2,
            category: vm.selected_category,
            approval_level: vm.approval_level
		}).then(res => {
		    vm.proposal = res.body;
			vm.$router.push({
			    name:"draft_proposal",
				params:{proposal_id:vm.proposal.id}
			});
            vm.creatingProposal = false;
		},
		err => {
			console.log(err);
		});
    },
    isDisabled: function() {
        let vm = this;
        if ((vm.org_applicant == '' && vm.yourself=='') ||( vm.selected_application_id == '')){
                return true;
            }
        return false;
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
    fetchApplicationTypes: function(){
		//let vm = this;

		this.$http.get(api_endpoints.application_types).then((response) => {
				//this.api_app_types = response.body;
				//console.log('api_app_types ' + response.body);
            for (let app_type of response.body) {
                this.application_types.push(app_type)
            }
                /*(
                for (var i = 0; i < this.api_app_types.length; i++) {
                    this.application_types.push({
                        text: this.api_app_types[i].name, 
                        value: this.api_app_types[i].id, 
                    });
                }
                */
		},(error) => {
			console.log(error);
		})
	},

    get_approval_level: function(category_name) {
        //let vm = this;
        for (var i = 0; i < vm.categories.length; i++) {
            if (category_name == this.categories[i]['text']) {
                vm.approval_level = this.categories[i]['approval'];
            }
        }
        
    }

  },
  mounted: function() {
    //let vm = this;
    this.fetchApplicationTypes();
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
</style>
