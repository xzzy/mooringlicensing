<template lang="html">
    <div v-if="vessel.vessel_details" class="container" id="internalVessel">
        <div class="row">
            <h3>{{ vessel.vessel_details.vessel_name}} - {{ vessel.rego_no }}</h3>
            <div class="col-md-3">
                <CommsLogs 
                    :comms_url="comms_url" 
                    :logs_url="logs_url" 
                    :comms_add_url="comms_add_url" 
                    :disable_add_entry="false"
                />
            </div>
            <div class="col-md-1"></div>
            <div class="col-md-8">
                <ul class="nav nav-pills mb-3" id="pills-tab" role="tablist">
                  <li class="nav-item">
                    <a class="nav-link active" id="pills-vessel-details-tab" data-toggle="pill" href="#pills-vessel-details" role="tab" aria-controls="pills-vessel-details" aria-selected="true">
                      Details
                    </a>
                  </li>
                  <li class="nav-item">
                    <a class="nav-link" id="pills-owners-tab" data-toggle="pill" href="#pills-owners" role="tab" aria-controls="pills-owners" aria-selected="false">
                      Owner(s)
                    </a>
                  </li>
                  <li class="nav-item">
                    <a class="nav-link" id="pills-bookings-permits-tab" data-toggle="pill" href="#pills-bookings-permits" role="tab" aria-controls="pills-bookings-permits" aria-selected="false">
                      Bookings/Permits
                    </a>
                  </li>
                </ul>

                <div class="tab-content" id="pills-tabContent">
                    <div class="tab-pane fade" id="pills-vessel-details" role="tabpanel" aria-labelledby="pills-vessel-details-tab">
                        <FormSection label="Registration details" Index="registration_details">
                            <div class="row form-group">
                                <div class="col-sm-3">
                                    <label>Registration number:</label>
                                </div>
                                <div class="col-sm-6">
                                    {{ vessel.rego_no }}
                                </div>
                            </div>

                            <div class="row form-group">
                                <div class="col-sm-3">
                                    <label>Name:</label>
                                </div>
                                <div class="col-sm-6">
                                    {{ vessel.vessel_details.vessel_name }}
                                </div>
                            </div>
                        </FormSection>
                        <FormSection label="Vessel details" Index="vessel_details">
                            <div class="row form-group">
                                <div class="col-sm-3">
                                    <label>Vessel length:</label>
                                </div>
                                <div class="col-sm-6">
                                    {{ vessel.vessel_details.vessel_length }}
                                </div>
                            </div>
                            <div class="row form-group">
                                <div class="col-sm-3">
                                    <label>Displacement tonnage:</label>
                                </div>
                                <div class="col-sm-6">
                                    {{ vessel.vessel_details.vessel_weight }}
                                </div>
                            </div>
                            <div class="row form-group">
                                <div class="col-sm-3">
                                    <label>Draft:</label>
                                </div>
                                <div class="col-sm-6">
                                    {{ vessel.vessel_details.vessel_draft }}
                                </div>
                            </div>
                            <div class="row form-group">
                                <div class="col-sm-3">
                                    <label>Type:</label>
                                </div>
                                <div class="col-sm-6">
                                    {{ vessel.vessel_details.vessel_type_display }}
                                </div>
                            </div>
                        </FormSection>
                    </div>
                    <div class="tab-pane fade" id="pills-owners" role="tabpanel" aria-labelledby="pills-owners-tab">
                        <FormSection label="Owner(s)" Index="owners">
                            <div v-if="vessel.id">
                                <datatable 
                                    ref="owners_datatable" 
                                    :id="datatable_id" 
                                    :dtOptions="owners_options" 
                                    :dtHeaders="owners_headers"
                                />
                            </div>
                        </FormSection>
                    </div>
                    <div class="tab-pane fade" id="pills-bookings-permits" role="tabpanel" aria-labelledby="pills-bookings-permits-tab">
                        <FormSection label="Bookings/Permits" Index="bookings_permits">
                            <div v-if="entity.id">
                                <BookingsPermits
                                :entity="entity"
                                :key="entity.id"
                                />
                            </div>
                        </FormSection>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import FormSection from '@/components/forms/section_toggle.vue'
import CommsLogs from '@common-utils/comms_logs.vue'
import BookingsPermits from '@common-utils/bookings_permits.vue'
import datatable from '@/utils/vue/datatable.vue'
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
    export default {
        name:'VesselDetails',
        components:{
            FormSection,
            CommsLogs,
            datatable,
            BookingsPermits,
        },
        data:function () {
            let vm = this;
            return {
                vessel: {
                    vessel_details: {
                    }
                },
                comms_url: helpers.add_endpoint_json(api_endpoints.vessel, this.$route.params.vessel_id + '/comms_log'),
                comms_add_url: helpers.add_endpoint_json(api_endpoints.vessel, this.$route.params.vessel_id + '/add_comms_log'),
                logs_url: helpers.add_endpoint_json(api_endpoints.vessel, this.$route.params.vessel_id + '/action_log'),
                datatable_id: 'owners-datatable-' + this._uid,
                owners_headers: ['Name', 'Company', 'Percentage', 'Phone', 'Start', 'End', 'Action'],

             }
        },
        computed: {
            entity: function() {
                return {
                    type: "vessel",
                    id: this.vessel.id,
                }
            },
            ownersUrl: function() {
                return `${api_endpoints.vessel}${this.vessel.id}/lookup_vessel_ownership?format=datatables`;
            },
            owners_options: function() {
                let vm = this;
                return {
                    searching: false,
                    autoWidth: false,
                    language: {
                        processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                    },
                    responsive: true,
                    ajax: {
                        "url": vm.ownersUrl,
                        "dataSrc": 'data',
                    },
                    dom: 'lBfrtip',
                    buttons:[],
                    columns: [
                        {
                            // 1. Name
                            data: "id",
                            orderable: false,
                            searchable: false,
                            visible: true,
                            'render': function(row, type, full){
                                return full.owner_full_name;
                            }
                        },
                        {
                            // 2. Company
                            data: "id",
                            orderable: true,
                            searchable: true,
                            visible: true,
                            'render': function(row, type, full){
                                let companyName = '';
                                if (full.company_ownership && full.company_ownership.company) {
                                    companyName = full.company_ownership.company.name;
                                }
                                return companyName;
                            }
                        },
                        {
                            // 3. Percentage
                            data: "id",
                            orderable: true,
                            searchable: true,
                            visible: true,
                            'render': function(row, type, full){
                                return full.applicable_percentage;
                            }
                        },
                        {
                            // 4. Phone
                            data: "id",
                            orderable: true,
                            searchable: true,
                            visible: true,
                            'render': function(row, type, full){
                                return full.owner_phone_number;
                            }
                        },
                        {
                            // 5. Start Date
                            data: "id",
                            orderable: true,
                            searchable: true,
                            visible: true,
                            'render': function(row, type, full){
                                return full.start_date;
                            }
                        },
                        {
                            // 6. End Date
                            data: "id",
                            orderable: true,
                            searchable: true,
                            visible: true,
                            'render': function(row, type, full){
                                return full.end_date;
                            }
                        },
                        {
                            // 7. Action
                            data: "id",
                            orderable: true,
                            searchable: true,
                            visible: true,
                            'render': function(row, type, full){
                                return `<a href='${full.action_link}'>View</a><br/>`;
                            }
                        },
                        ],
                    processing: true,
                    initComplete: function() {
                        console.log('in initComplete')
                    },
                }
            },

        },
        methods:{
            setTabs:function(){
                let vm = this;
                /* set Applicant tab Active */
                $('#pills-tab a[href="#pills-vessel-details"]').tab('show');
                // ensure datatables in tabs are responsive
                $('#pills-owners-tab').on('shown.bs.tab', function (e) {
                    vm.$refs.owners_datatable.vmDataTable.columns.adjust().responsive.recalc();
                });
            },
        },
        mounted: function () {
            this.$nextTick(async () => {
                this.setTabs();
            });
        },
        created: async function() {
            const res = await this.$http.get(`/api/vessel/${this.$route.params.vessel_id}/full_details.json`);
            this.vessel = Object.assign({}, res.body);

        },
    }
</script>

<style lang="css" scoped>
    .section{
        text-transform: capitalize;
    }
    .list-group{
        margin-bottom: 0;
    }
    .fixed-top{
        position: fixed;
        top:56px;
    }

    .nav-item {
        background-color: rgb(200,200,200,0.8) !important;
        margin-bottom: 2px;
    }

    .nav-item>li>a {
        background-color: yellow !important;
        color: #fff;
    }

    .nav-item>li.active>a, .nav-item>li.active>a:hover, .nav-item>li.active>a:focus {
      color: white;
      background-color: blue;
      border: 1px solid #888888;
    }

	.admin > div {
	  display: inline-block;
	  vertical-align: top;
	  margin-right: 1em;
	}

</style>

