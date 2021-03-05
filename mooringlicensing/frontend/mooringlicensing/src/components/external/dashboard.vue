<template>
<div class="container" id="externalDash">
    <div class="row">
        <div class="col-sm-12">

        </div>
    </div>
    <!--
    <ProposalDashTable level='external' :url='proposals_url'/>
    <ApprovalDashTable level='external' :url='approvals_url'/>
    <ComplianceDashTable level='external' :url='compliances_url'/>
    -->
</div>
</template>
<script>

import datatable from '@/utils/vue/datatable.vue'
//import ProposalDashTable from '@common-utils/proposals_dashboard.vue'
//import ApprovalDashTable from '@common-utils/approvals_dashboard.vue'
//import ComplianceDashTable from '@common-utils/compliances_dashboard.vue'
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
export default {
    name: 'ExternalDashboard',
    data() {
        let vm = this;
        return {
            empty_list: '/api/empty_list',
            //proposals_url: helpers.add_endpoint_json(api_endpoints.proposals,'user_list'),
            //approvals_url: helpers.add_endpoint_json(api_endpoints.approvals,'user_list'),
            //compliances_url: helpers.add_endpoint_json(api_endpoints.compliances,'user_list'),

            proposals_url: api_endpoints.proposals_paginated_external,
            approvals_url: api_endpoints.approvals_paginated_external,
            compliances_url: api_endpoints.compliances_paginated_external,

            system_name: api_endpoints.system_name,
            apiaryTemplateGroup: false,
            dasTemplateGroup: false,
            // from env var?
            apiarySystemName: 'Apiary System',
            dasSystemName: 'Disturbance Assessment System',
        }
    },
    components:{
        //ProposalDashTable,
        //ApprovalDashTable,
        //ComplianceDashTable
    },
    watch: {},
    computed: {

    },
    methods: {
        
    },
    mounted: function () {

    },
    created: function() {
        // retrieve template group
        //this.$http.get('/template_group',{
        //    emulateJSON:true
        //    }).then(res=>{
        //        //this.template_group = res.body.template_group;
        //        if (res.body.template_group === 'apiary') {
        //            this.apiaryTemplateGroup = true;
        //        } else {
        //            this.dasTemplateGroup = true;
        //        }
        //},err=>{
        //    console.log(err);
        //});
    },

}
</script>
