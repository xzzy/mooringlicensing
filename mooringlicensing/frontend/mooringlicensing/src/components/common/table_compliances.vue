<template>
    <div>
        <div class="row">

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
            filterApplicationType: null,
            filterApplicationStatus: null,

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

    },
    created: function(){

    },
    mounted: function(){

    }
}
</script>
