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

        <!--div-->
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
                                    <label>Overall length of vessel:</label>
                                </div>
                                <div class="col-sm-6">
                                    {{ vessel.vessel_details.vessel_overall_length }}
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
                                    {{ vessel.vessel_details.vessel_type_display }}
                                </div>
                            </div>
                        </FormSection>
                    </div>
                    <div class="tab-pane fade" id="pills-owners" role="tabpanel" aria-labelledby="pills-owners-tab">
                        <FormSection label="Owner(s)" Index="owners">
                        </FormSection>
                    </div>
                    <div class="tab-pane fade" id="pills-bookings-permits" role="tabpanel" aria-labelledby="pills-bookings-permits-tab">
                        <FormSection label="Bookings/Permits" Index="bookings_permits">
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
        },
         data:function () {
            return {
                vessel: {
                    vessel_details: {
                    }
                },
                comms_url: helpers.add_endpoint_json(api_endpoints.vessel, this.$route.params.vessel_id + '/comms_log'),
                comms_add_url: helpers.add_endpoint_json(api_endpoints.vessel, this.$route.params.vessel_id + '/add_comms_log'),
                logs_url: helpers.add_endpoint_json(api_endpoints.vessel, this.$route.params.vessel_id + '/action_log'),
             }
        },
        computed: {
        },
        methods:{
            setTabs:function(){
                let vm = this;

                /* set Applicant tab Active */
                $('#pills-tab a[href="#pills-vessel-details"]').tab('show');

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
        /*
        beforeRouteEnter: async function(to, from, next) {
            if (to.params.mooring_id) {
                const res = await this.$http.get(`/api/mooring/${to.params.mooring_id}.json`);
                this.mooring = Object.assign({}, res.body);
            }
        },
        */

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

