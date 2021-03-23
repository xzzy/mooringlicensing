<template>
    <div>
        <div class="row">

        </div>

        <div class="row">
            <div class="col-lg-12">
                <datatable 
                    ref="to_be_endorsed_datatable" 
                    :id="datatable_id" 
                    :dtOptions="to_be_endorsed_options" 
                    :dtHeaders="to_be_endorsed_headers"
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
    props: {
        level:{
            type: String,
            required: true,
            validator: function(val) {
                let options = ['internal', 'referral', 'external'];
                return options.indexOf(val) != -1 ? true: false;
            }
        },
    },
    data() {
        let vm = this;
        return {
            datatable_id: 'to_be_endorsed-datatable-' + vm._uid,

            // selected values for filtering
            filterApplicationType: null,
            filterApplicationStatus: null,

            // Datatable settings
            to_be_endorsed_headers: ['Number', 'Mooring', 'Applicant', 'Status', 'Action'],
            to_be_endorsed_options: {
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
        is_external: function() {
            return this.level == 'external'
        },

    },
    methods: {

    },
    created: function(){

    },
    mounted: function(){

    }
}
</script>
