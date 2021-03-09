<template>
    <div>
        <div class="row">
            <div class="col-md-3">
                <div class="form-group">
                    <label for="">Type</label>
                    <select class="form-control" v-model="filterApplicationType">
                        <option value="All">All</option>
                        <option v-for="r in application_types" :value="r">{{r}}</option>
                    </select>
                </div>
            </div>
            <div class="col-md-3">
                <div class="form-group">
                    <label for="">Status</label>
                    <select class="form-control" v-model="filterApplicationStatus">
                        <option value="All">All</option>
                        <option v-for="a in application_statuses" :value="a">{{a}}</option>
                    </select>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-12">
                <button type="button" class="btn btn-primary pull-right">New Application</button>
            </div>
        </div>

        <div class="row">
            <div class="col-lg-12">
                <datatable 
                    ref="application_datatable" 
                    :id="datatable_id" 
                    :dtOptions="application_options" 
                    :dtHeaders="application_headers"
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
    name: 'TableApplications',
    data() {
        let vm = this;
        return {
            datatable_id: 'applications-datatable-' + vm._uid,

            // selected values for filtering
            filterApplicationType: null,
            filterApplicationStatus: null,

            // filtering options
            application_types: ['test1', 'test2'],
            application_statuses: ['test3', 'test4'],

            // Datatable settings
            application_headers: ['id', 'Number', 'Type', 'Application Type', 'Status', 'Lodged', 'Action'],
            application_options: {
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
