<template>
<div class="container" id="internalApproval">
    <div class="row">
        <h3>Licence {{ approval.lodgement_number }}</h3>
        <div class="col-md-3">
            <CommsLogs :comms_url="comms_url" :logs_url="logs_url" :comms_add_url="comms_add_url" :disable_add_entry="false"/>
            <div class="row">
                <div class="panel panel-default">
                    <div class="panel-heading">
                       Submission
                    </div>
                    <div class="panel-body panel-collapse">
                        <div class="row">

                            <div class="col-sm-12 top-buffer-s">
                                <strong>Issued on</strong><br/>
                                {{ approval.issue_date | formatDate}}
                            </div>
                            <div class="col-sm-12 top-buffer-s">
                                <table class="table small-table">
                                    <tr>
                                        <th>Lodgement</th>
                                        <th>Date</th>
                                        <th>Action</th>
                                    </tr>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="panel panel-default">
                    <div class="panel-heading">
                        Workflow
                    </div>
                    <div class="panel-body panel-collapse">
                        <div class="row">
                            <div class="col-sm-12">
                                <strong>Status</strong><br/>
                                {{ approval.status }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-1"></div>
        <div class="col-md-8">
            <div class="row">
                <div v-if="approval && approval.submitter">
                    <Applicant
                        :email_user="approval.submitter" 
                        applicantType="SUB" 
                        id="approvalSubmitterDetails"
                        :readonly="true"
                        customerType="holder"
                    />
                </div>
            </div>

            <div class="row">

                <div class="panel panel-default">
                  <div class="panel-heading">
                    <h3 class="panel-title">Licence Details
                        <a class="panelClicker" :href="'#'+oBody" data-toggle="collapse" expanded="true"  data-parent="#userInfo" :aria-controls="oBody">
                            <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                        </a>
                    </h3>
                  </div>
                  <div v-if="loading.length == 0" class="panel-body collapse" :id="oBody">
                      <form class="form-horizontal" action="index.html" method="post">
                          <div class="form-group">
                            <label for="" class="col-sm-3 control-label">Issue Date</label>
                            <div class="col-sm-6">
                                <label for="" class="control-label pull-left">{{approval.issue_date | formatDate}}</label>
                            </div>
                        <!---    <div class="col-sm-6">
                                <p>{{approval.issue_date | formatDate}}</p>
                            </div> -->
                          </div>
                          <div class="form-group">
                            <label for="" class="col-sm-3 control-label" >Start Date</label>
                            <div class="col-sm-6">
                                <label for="" class="control-label pull-left">{{approval.start_date | formatDate}}</label>
                            </div>
                          </div>
                          <div class="form-group">
                            <label for="" class="col-sm-3 control-label">Expiry Date</label>
                            <div class="col-sm-3">
                                <label for="" class="control-label pull-left">{{approval.expiry_date | formatDate}}</label>
                            </div>

                          </div>
                          <div class="form-group">
                            <label for="" class="col-sm-3 control-label" >Document</label>
                            <div class="col-sm-4">
                                <!-- <p><a target="_blank" :href="approval.licence_document" class="control-label pull-left">Approval.pdf</a></p> -->
                                <!--p><a :href="'#'+approval.id" class="control-label pull-left" @click="viewApprovalPDF(approval.id, approval.latest_apiary_licence_document)">Approval.pdf</a></p-->
                                <p><a target="_blank" :href="approval.licence_document" class="control-label pull-left">Licence.pdf</a></p>
                            </div>
                          </div>
                          <!--div class="form-group">
                            <label for="" class="col-sm-3 control-label" >Document History</label>
                            <div class="col-sm-4">
                                <div v-for="doc in approval.apiary_licence_document_history">
                                    <p><a target="_blank" :href="doc.url" class="control-label pull-left">{{doc.name}}</a></p>
                                </div>
                            </div>
                          </div-->
                       </form>
                  </div>
                </div>
            </div>
            <div class="row" v-if="approval && approval.submitter && approval.current_proposal">
                  <Vessels
                  :proposal="approval.current_proposal"
                  :profile="approval.submitter"
                  id="approvalVessel"
                  ref="vessel"
                  :readonly="true"
                  :is_internal="true"
                  />
            </div>

        </div>
    </div>
</div>
</template>
<script>
import $ from 'jquery'
import Vue from 'vue'
//import datatable from '@vue-utils/datatable.vue'
import CommsLogs from '@common-utils/comms_logs.vue'
import Applicant from '@/components/common/applicant.vue'
import Vessels from '@/components/common/vessels.vue'
//import ResponsiveDatatablesHelper from "@/utils/responsive_datatable_helper.js"
import FormSection from "@/components/forms/section_toggle.vue"
import { api_endpoints, helpers } from '@/utils/hooks'
//import OnSiteInformation from '@/components/common/apiary/section_on_site_information.vue'
//import TemporaryUse from '@/components/common/apiary/section_temporary_use.vue'
//import ComponentSiteSelection from '@/components/common/apiary/component_site_selection.vue'
//import SectionAnnualRentalFee from '@/components/common/apiary/section_annual_rental_fee.vue'
export default {
  name: 'ApprovalDetail',
  data() {
    let vm = this;
    return {
        loading: [],
        approval: {
            applicant_id: null

        },
        DATE_TIME_FORMAT: 'DD/MM/YYYY HH:mm:ss',
        adBody: 'adBody'+vm._uid,
        pBody: 'pBody'+vm._uid,
        cBody: 'cBody'+vm._uid,
        oBody: 'oBody'+vm._uid,
        org: {
            address: {}
        },

        // Filters
        logs_url: helpers.add_endpoint_json(api_endpoints.approvals,vm.$route.params.approval_id+'/action_log'),
        comms_url: helpers.add_endpoint_json(api_endpoints.approvals,vm.$route.params.approval_id+'/comms_log'),
        comms_add_url: helpers.add_endpoint_json(api_endpoints.approvals,vm.$route.params.approval_id+'/add_comms_log'),
    }
  },
  watch: {},
  filters: {
    formatDate: function(data){
        return moment(data).format('DD/MM/YYYY');
    }
  },
    props: {
        approvalId: {
            type: Number,
        },
    },
  created: function(){
    //Vue.http.get(helpers.add_endpoint_json(api_endpoints.approvals,this.approvalId)).then((response) => {
    //console.log(this.$
    Vue.http.get(helpers.add_endpoint_json(api_endpoints.approvals,this.$route.params.approval_id)).then((response) => {
        this.approval = response.body;
        this.approval.applicant_id = response.body.applicant_id;
        if (this.approval.submitter.postal_address == null){ this.approval.submitter.postal_address = {}; }
    },(error) => {
        console.log(error);
    })
  },
  components: {
        //SectionAnnualRentalFee,
        //datatable,
        CommsLogs,
        FormSection,
        Applicant,
        Vessels,
        //OnSiteInformation,
        //TemporaryUse,
        //ComponentSiteSelection,
  },
  computed: {
    isLoading: function () {
      return this.loading.length > 0;
    },
      /*
    proposal: function() {
        if (this.approval && this.approval.current_proposal_number){
            return ({
                "id": this.approval.current_proposal_number,
            })
        }
    },
    */

  },
  methods: {
    commaToNewline(s){
        return s.replace(/[,;]/g, '\n');
    },
      /*
    fetchOrganisation(applicant_id){
        let vm=this;
        Vue.http.get(helpers.add_endpoint_json(api_endpoints.organisations,applicant_id)).then((response) => {

            vm.org = response.body;
            vm.org.address = response.body.address;
    },(error) => {
        console.log(error);
    })

    },
    */
    viewApprovalPDF: function(id,media_link){
            let vm=this;
            //console.log(approval);
            vm.$http.get(helpers.add_endpoint_json(api_endpoints.approvals,(id+'/approval_pdf_view_log')),{
                })
                .then((response) => {
                    //console.log(response)
                }, (error) => {
                    console.log(error);
                });
            window.open(media_link, '_blank');
    },


  },
  mounted: function () {
    let vm = this;
  }
}
</script>
<style scoped>
.top-buffer-s {
    margin-top: 10px;
}
.actionBtn {
    cursor: pointer;
}
.hidePopover {
    display: none;
}
</style>
