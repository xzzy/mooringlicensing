<template lang="html">
    <div class="container" >
        <div class="row">
            <div class="col-sm-12">
                <form class="form-horizontal" name="personal_form" method="post">
                    <FormSection label="Apply for">
                        <div>
                            <!--label for="" class="control-label" >Licence Type * <a :href="proposal_type_help_url" target="_blank"><i class="fa fa-question-circle" style="color:blue">&nbsp;</i></a></label-->
                            <label>Do you want to apply</label>
                            <div class="col-sm-12">
                                <div class="form-group">
                                    <select class="form-control" style="width:50%" v-model="selectedApplication">
                                        <!--option value="" selected disabled>Select Licence type*</option-->
                                        <option v-for="application_type in application_types" :value="application_type">
                                            {{ application_type.new_application_text }}
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
    submit: function() {
        //let vm = this;
        swal({
            title: "Create " + this.selectedApplication.description,
            text: "Are you sure you want to create " + this.alertText + "?",
            type: "question",
            showCancelButton: true,
            confirmButtonText: 'Accept'
        }).then(() => {
            /*
            if (!vm.has_active_proposals()) {
         	    vm.createProposal();
            }
            */
        },(error) => {
        });
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
        this.$http.get(api_endpoints.application_types_dict+'?apply_page=True').then((response) => {
            for (let app_type of response.body) {
                this.application_types.push(app_type)
            }
		},(error) => {
			console.log(error);
		})
	},

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
