<template>
    <div class="container" id="externalDash">
        <FormSection :formCollapse="false" label="Vessels" Index="vessels">
            <div class="row">
                <div class="col-sm-10">
                </div>
                <div class="col-sm-2">
                    <button type="button" class="btn btn-primary pull-right" @click="addVessel">Add Vessel</button>
                </div>
                <!--div class="col-sm-1">
                </div-->
            </div>

            <datatable 
                ref="vessels_datatable" 
                id="vessels_datatable" 
                :dtOptions="datatable_options" 
                :dtHeaders="datatable_headers"
            />
        </FormSection>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue'
import FormSection from "@/components/forms/section_toggle.vue"
import { api_endpoints, helpers } from '@/utils/hooks'

export default {
    name: 'VesselsDashboard',
    data() {
        let vm = this;
        return {
            // Datatable settings
            datatable_headers: ['Name', 'Registration', 'Length', 'Draft', 'Type', 'Action'],
            datatable_options: {
                autoWidth: false,
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                serverSide: true,
                searching: true,
                ajax: {
                    "url": api_endpoints.vessel_external_list + '?format=datatables',
                    "dataSrc": 'data',

                    // adding extra GET params for Custom filtering
                    "data": function ( d ) {
                        /*
                        d.filter_application_type = vm.filterApplicationType;
                        d.filter_application_status = vm.filterApplicationStatus;
                        */
                    }
                },
                dom: 'lBfrtip',
                buttons:[
                    //{
                    //    extend: 'excel',
                    //    exportOptions: {
                    //        columns: ':visible'
                    //    }
                    //},
                    //{
                    //    extend: 'csv',
                    //    exportOptions: {
                    //        columns: ':visible'
                    //    }
                    //},
                ],
                columns: [
                    {
                        // 1. ID
                        data: "vessel_name",
                        orderable: false,
                        searchable: false,
                        visible: true,
                        /*
                        'render': function(row, type, full){
                            return full.id
                        }
                        */
                    },
                    {
                        // 2. Lodgement Number
                        data: "rego_no",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        /*
                        'render': function(row, type, full){
                            return full.lodgement_number
                        }
                        */
                    },
                    {
                        // 3. Type (This corresponds to the 'ApplicationType' at the backend)
                        data: "vessel_length",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        /*
                        'render': function(row, type, full){
                            return full.application_type_dict.description
                        }
                        */
                    },
                    {
                        // 4. Application Type (This corresponds to the 'ProposalType' at the backend)
                        data: "vessel_draft",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        /*
                        'render': function(row, type, full){
                            return full.proposal_type.description
                        }
                        */
                    },
                    {
                        // 5. Status
                        data: "vessel_type",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        /*
                        'render': function(row, type, full){
                            return full.customer_status
                        }
                        */
                    },
                    {
                        // 8. Action
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            console.log(full)
                            return 'wip';
                            /*
                            let links = '';
                            if (!vm.is_external){
                                if(full.assessor_process){
                                    links +=  `<a href='/internal/proposal/${full.id}'>Process</a><br/>`;
                                } else {
                                    links +=  `<a href='/internal/proposal/${full.id}'>View</a><br/>`;
                                }
                            }
                            else{
                                if (full.can_user_edit) {
                                    links +=  `<a href='/external/proposal/${full.id}'>Continue</a><br/>`;
                                    links +=  `<a href='#${full.id}' data-discard-proposal='${full.id}'>Discard</a><br/>`;
                                }
                                else if (full.can_user_view) {
                                    links +=  `<a href='/external/proposal/${full.id}'>View</a><br/>`;
                                }
                            }
                            return links;
                            */
                        }
                    },
                ],
                processing: true,
                initComplete: function() {
                    console.log('in initComplete')
                },
            },
        }
    },
    components:{
        FormSection,
        datatable
    },
    watch: {

    },
    computed: {
    },
    methods: {
        addVessel: function() {
        },
    },
    mounted: function () {

    },
    created: function() {

    },
}
</script>
<style lang="css" scoped>
    button {
        width: 100%;
        height: 100%;
    }
</style>
