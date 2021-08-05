<template>
<div class="container" id="internalApproval">
    <div class="row">
        <h3>{{ approvalLabel }}: {{ approval.lodgement_number }}</h3>
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
                      <h3 class="panel-title">{{ approvalLabel }}
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
                              <label for="" class="col-sm-3 control-label" >{{ approvalLabel }}</label>
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
            <div class="row" v-if="approval && approval.submitter && approval.current_proposal && annualAdmissionPermit">
                  <Vessels
                  :proposal="approval.current_proposal"
                  :profile="approval.submitter"
                  id="approvalVessel"
                  ref="vessel"
                  :readonly="true"
                  :is_internal="true"
                  />
            </div>
            <div class="row" v-if="approval && approval.id && authorisedUserPermit">
                <FormSection 
                    :formCollapse="false" 
                    label="Moorings" 
                    Index="moorings"
                >
                    <datatable
                        ref="moorings_datatable"
                        :id="moorings_datatable_id"
                        :dtOptions="moorings_datatable_options"
                        :dtHeaders="moorings_datatable_headers"
                    />
                </FormSection>
            </div>
            <div class="row" v-if="approval && approval.id && mooringLicence">
                <FormSection 
                    :formCollapse="false" 
                    label="Vessels" 
                    Index="mooringLicenceVessels"
                >
                    <datatable
                        ref="ml_vessels_datatable"
                        :id="ml_vessels_datatable_id"
                        :dtOptions="ml_vessels_datatable_options"
                        :dtHeaders="ml_vessels_datatable_headers"
                    />
                </FormSection>
            </div>

        </div>
    </div>
</div>
</template>
<script>
import $ from 'jquery'
import Vue from 'vue'
import datatable from '@vue-utils/datatable.vue'
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
        moorings_datatable_id: 'moorings-datatable-' + vm._uid,
        ml_vessels_datatable_id: 'ml-vessels-datatable-' + vm._uid,
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
        moorings_datatable_headers: [
                //'Id',
                'Mooring',
                'Licensee',
                'Mobile',
                'Email',
            ],

        moorings_datatable_options: {
            columns: [
                {
                    data: "mooring_name",
                },
                {
                    data: "licensee",
                },
                {
                    data: "mobile",
                },
                {
                    data: "email",
                },
            ],
        },
        ml_vessels_datatable_headers: [
                //'Id',
                'Vessel',
                'Sticker',
                'Owner',
                'Mobile',
                'Email',
            ],

        ml_vessels_datatable_options: {
            columns: [
                {
                    data: "vessel_name",
                },
                {
                    data: "sticker_name",
                },
                {
                    data: "owner",
                },
                {
                    data: "mobile",
                },
                {
                    data: "email",
                },
            ],
        },

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
  created: async function(){
      const response = await Vue.http.get(helpers.add_endpoint_json(api_endpoints.approvals,this.$route.params.approval_id));
      this.approval = Object.assign({}, response.body);
      this.approval.applicant_id = response.body.applicant_id;
      if (this.approval.submitter.postal_address == null){ this.approval.submitter.postal_address = {}; }
      await this.$nextTick(() => {
          if (this.approval && this.approval.id && this.authorisedUserPermit) {
              this.constructMooringsTable();
          }
          if (this.approval && this.approval.id && this.mooringLicence) {
              this.constructMLVesselsTable();
          }
      })
  },
  components: {
        datatable,
        CommsLogs,
        FormSection,
        Applicant,
        Vessels,
  },
  computed: {
    isLoading: function () {
      return this.loading.length > 0;
    },
    approvalLabel: function() {
        let description = '';
        if (this.approval && this.approval.approval_type_dict) {
            description = this.approval.approval_type_dict.description;
        }
        return description;
    },
    annualAdmissionPermit: function() {
        let permit = false;
        if (this.approval && this.approval.approval_type_dict && this.approval.approval_type_dict.code === 'aap') {
            permit = true;
        }
        return permit;
    },
    authorisedUserPermit: function() {
        let permit = false;
        if (this.approval && this.approval.approval_type_dict && this.approval.approval_type_dict.code === 'aup') {
            permit = true;
        }
        return permit;
    },
    mooringLicence: function() {
        let permit = false;
        if (this.approval && this.approval.approval_type_dict && this.approval.approval_type_dict.code === 'ml') {
            permit = true;
        }
        return permit;
    },

  },
  methods: {
    constructMooringsTable: function() {
        let vm = this;
        this.$refs.moorings_datatable.vmDataTable.clear().draw();

        for(let aum of vm.approval.authorised_user_moorings_detail) {
            this.$refs.moorings_datatable.vmDataTable.row.add(
                {
                    'mooring_name': aum.mooring_name,
                    'licensee': aum.licensee,
                    'mobile': aum.mobile,
                    'email': aum.email,
                }
            ).draw();
        }
    },
    constructMLVesselsTable: function() {
        let vm = this;
        this.$refs.ml_vessels_datatable.vmDataTable.clear().draw();

        for(let mlv of vm.approval.mooring_licence_vessels_detail) {
            this.$refs.ml_vessels_datatable.vmDataTable.row.add(
                {
                    'vessel_name': mlv.vessel_name,
                    'sticker_name': mlv.sticker_name,
                    'owner': mlv.owner,
                    'mobile': mlv.mobile,
                    'email': mlv.email,
                }
            ).draw();
        }
    },

    commaToNewline(s){
        return s.replace(/[,;]/g, '\n');
    },
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
  },
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
