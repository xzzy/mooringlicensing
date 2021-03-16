<template>
    <div>
        <div class="row">

        </div>

        <div class="row">
            <div class="col-lg-12">
                <datatable 
                    ref="licences_and_permits_datatable" 
                    :id="datatable_id" 
                    :dtOptions="licences_and_permits_options" 
                    :dtHeaders="licences_and_permits_headers"
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
    name: 'TableLicencesAndPermits',
    data() {
        let vm = this;
        return {
            datatable_id: 'licences_and_permits-datatable-' + vm._uid,

            // selected values for filtering
            //filterApplicationType: null,
            //filterApplicationStatus: null,

            // Datatable settings
            licences_and_permits_headers: ['Number', 'Type', 'Sticker Number', 'Status', 'Issue Date', 'Expiry Date', 'Vessel', 'Action'],
            licences_and_permits_options: {
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
