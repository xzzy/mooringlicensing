<template>
    <div>
        <div class="row">
            <div class="col-md-3">
                <div class="form-group">
                    <label for="">Status</label>
                    <select class="form-control" v-model="filterComplianceStatus">
                        <option value="All">All</option>
                        <option v-for="status in compliance_statuses" :value="status.code">{{ status.description }}</option>
                    </select>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-lg-12">
                <datatable 
                    ref="compliances_datatable" 
                    :id="datatable_id" 
                    :dtOptions="compliances_options" 
                    :dtHeaders="compliances_headers"
                />
            </div>
        </div>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue'
import Vue from 'vue'
import { api_endpoints, helpers }from '@/utils/hooks'
export default {
    name: 'TableCompliances',
    data() {
        let vm = this;
        return {
            datatable_id: 'compliances-datatable-' + vm._uid,

            // selected values for filtering
            filterComplianceStatus: null,
            compliance_statuses: [],

            // Datatable settings
            compliances_headers: ['Number', 'Licence/Permit', 'Condition', 'Due Date', 'Status', 'Action'],
            compliances_options: {
                searching: false

                // TODO: retrieve contents

            },
        }
    },
    components:{
        datatable
    },
    watch: {

    },
    computed: {

    },
    methods: {
        fetchFilterLists: function(){
            let vm = this;

            // Statuses
            vm.$http.get(api_endpoints.compliance_statuses_dict).then((response) => {
                vm.compliance_statuses = response.body
            },(error) => {
                console.log(error);
            })
        },
    },
    created: function(){
        this.fetchFilterLists()
    },
    mounted: function(){

    }
}
</script>
