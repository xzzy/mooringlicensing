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
            <div v-if="recordSaleId">
                <RecordSale 
                ref="record_sale" 
                :recordSaleId="recordSaleId"
                :key="recordSaleKey"
                @closeModal="closeModal"
                />
            </div>
        </FormSection>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue'
import FormSection from "@/components/forms/section_toggle.vue"
import { api_endpoints, helpers } from '@/utils/hooks'
import RecordSale from './record_sale.vue'

export default {
    name: 'VesselsDashboard',
    data() {
        let vm = this;
        return {
            recordSaleId: null,
            uuid: 0,
            // Datatable settings
            datatable_headers: ['Name', 'Registration', 'Length', 'Draft', 'Type', 'Owner', 'Action'],
            datatable_options: {
                autoWidth: false,
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                //serverSide: true,
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
                        data: "vessel_details.vessel_name",
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
                        data: "vessel_details.rego_no",
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
                        data: "vessel_details.vessel_length",
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
                        data: "vessel_details.vessel_draft",
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
                        data: "vessel_details.vessel_type",
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
                        // 5. Status
                        data: "owner_name",
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
                        //data: "vessel_details.vessel_id",
                        data: "id",
                        orderable: true,
                        searchable: true,
                        visible: true,
                        'render': function(row, type, full){
                            let links = '';
                            links += `<a href='/external/vesselownership/${full.id}'>Edit</a><br/>`;
                            //links += `<a id="record_sale_${full.id}" href=#>Record Sale</a><br/>`;
                            links += full.record_sale_link;
                            return links
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
        datatable,
        RecordSale,
    },
    watch: {
    },
    computed: {
        recordSaleKey: function() {
            return `${this.recordSaleId}_${this.uuid}`
        },
    },
    methods: {
        closeModal: function() {
            this.uuid++;
        },
        addVessel: function() {
            this.$router.push({
                name: 'new-vessel'
            });
        },
        /*
        actionShortcut: async function(id, approvalType) {
            let vm = this;
            let processingTableStr = `.action-${id}`;
            let processViewStr = `.process-view-${id}`;
            let processingTable = $(processingTableStr);
            let processView = $(processViewStr);
            processingTable.replaceWith("<div><i class='fa fa-2x fa-spinner fa-spin'></i></div>");
            processView.replaceWith("");
            let post_url = '/api/feewaivers/' + id + '/final_approval/'
            let res = await Vue.http.post(post_url, {'approval_type': approvalType});
            if (res.ok) {
                // this should also be await?
                await this.refreshFromResponse();
            }
        },
        */
        refreshFromResponse: async function(){
            await this.$refs.vessels_datatable.vmDataTable.ajax.reload();
        },

        openSaleModal: function() {
            this.$nextTick(() => {
                console.log(this.recordSaleId)
                this.$refs.record_sale.isModalOpen = true;
            });
        },
        addEventListeners: function() {
            let vm = this;
            let table = vm.$refs.vessels_datatable.vmDataTable
            /*
            table.on('processing.dt', function(e) {
            })
            */
            table.on('click', 'a[data-id]', async function(e) {
                e.preventDefault();
                var id = $(this).attr('data-id');
                //await vm.actionShortcut(id, 'issue');
                vm.recordSaleId = parseInt(id);
                vm.openSaleModal();
            });
            /*
            let recordSale = $('#record_sale_96');
            recordSale.on('click', () => {
                console.log("record sale")
            })
            */
        }
    },
    mounted: function () {
        this.$nextTick(() => {
            this.addEventListeners();
        });

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
