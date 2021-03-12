<template>
    <div>
        <div class="row">
            <div class="col-lg-12">
                <input type="checkbox"> Show expired and/or surrendered waiting list allocations
            </div>
        </div>

        <div class="row">
            <div class="col-lg-12">
                <datatable 
                    ref="waiting_list_datatable" 
                    :id="datatable_id" 
                    :dtOptions="waiting_list_options" 
                    :dtHeaders="waiting_list_headers"
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
    name: 'TableWaitingList',
    data() {
        let vm = this;
        return {
            datatable_id: 'waiting_lists-datatable-' + vm._uid,

            // selected values for filtering
            //filterApplicationType: null,
            //filterApplicationStatus: null,

            // Datatable settings
            waiting_list_headers: ['Number', 'Bay', 'Application number in Bay', 'Status', 'Vessel Registration', 'Vessel Name', 'Issue Date', 'Expiry Date', 'Action'],
            waiting_list_options: {
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

    },
    created: function(){

    },
    mounted: function(){

    }
}
</script>
