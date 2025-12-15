<template>
    <div>
        <div class="row">
            <div class="col-md-3">
                <div class="form-group">
                    <label for="">Fee Source type</label>
                    <select class="form-control" v-model="filterFeeSourceType">
                        <option value="All">All</option>
                        <option v-for="type in fee_source_types" :value="type.code">{{ type.description }}</option>
                    </select>
                </div>
            </div>
            <div class="col-md-3">
                <div class="form-group">
                    <label for="">Status</label>
                    <select class="form-control" v-model="filterStatus">
                        <option value="All">All</option>
                        <option v-for="invoice_status in invoice_statuses" :value="invoice_status.code">{{ invoice_status.display }}</option>
                    </select>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-lg-12">
                <datatable
                    ref="invoices_datatable"
                    :id="datatable_id"
                    :dtOptions="datatable_options"
                    :dtHeaders="datatable_headers"
                />
            </div>
        </div>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue'
import { api_endpoints, helpers } from '@/utils/hooks'
export default {
    name: 'TableInvoices',
    data() {
        let vm = this;
        return {
            datatable_id: 'invoices-datatable-' + vm._uid,
            approvalTypesToDisplay: ['aap', 'aup', 'ml'],

            // selected values for filtering
            filterFeeSourceType: null,
            filterStatus: null,

            // filtering options
            fee_source_types: [],
            invoice_statuses: [],
        }
    },
    components:{
        datatable
    },
    watch: {
        filterFeeSourceType: function() {
            this.$refs.invoices_datatable.vmDataTable.draw();
        },
        filterStatus: function(){
            this.$refs.invoices_datatable.vmDataTable.draw();
        },
    },
    computed: {
        number_of_columns: function() {
            return this.datatable_headers.length
        },
        datatable_headers: function(){
            return ['id','Invoice Reference','Fee Source', 'Fee Source Type', 'Created At', 'Settles At', 'Amount', 'Description']
        },
        column_id: function(){
            return {
                // 1. ID
                data: "id",
                orderable: false,
                searchable: false,
                visible: false,
                'render': function(row, type, full){
                    return full.id
                }
            }
        },
        datatable_options: function(){
            let vm = this

            let columns = [
                vm.column_id,
            ]
            let search = true

            return {
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                rowCallback: function (row, sticker){
                    let row_jq = $(row)
                    row_jq.attr('id', 'invocie_id_' + invoice.id)
                    row_jq.children().first().addClass(vm.td_expand_class_name)

                },
                autoWidth: true,
                responsive: true,
                serverSide: true,
                paging: true,
                lengthMenu: [ [10, 25, 50, 100, -1], [10, 25, 50, 100, "All"] ],
                searching: search,
                ordering: true,
                order: [[1, 'desc']],  // Default order [[column_index, 'asc/desc'], ...]
                ajax: {
                    "url": api_endpoints.invoices_paginated_list + '?format=datatables',
                    "dataSrc": 'data',

                    // adding extra GET params for Custom filtering
                    "data": function ( d ) {
                        d.filter_approval_type = vm.filterFeeSourceType
                        d.filter_sticker_status = vm.filterStatus
                        d.level = vm.level

                        //only use columns necessary for filtering and ordering
                        let keepCols = []
                        let originalCols = d.columns
                        d.columns.forEach((value, index) => {
                            if (value.searchable || value.orderable) {
                                keepCols.push(d.columns[index])
                            }
                        });
                        d.columns = keepCols;

                        //adjust order
                        let nameIndexDict = {}
                        d.columns.forEach((value, index) => {
                                nameIndexDict[value.name] = index;
                            }
                        )
                        let originalNameIndexDict = {}
                        originalCols.forEach((value, index) => {
                                originalNameIndexDict[value.name] = index;
                            }
                        )
                        let newOrder = JSON.parse(JSON.stringify(d.order));
                        d.order.forEach((o_value, o_index) => {
                            Object.entries(originalNameIndexDict).forEach(([key,value]) => {
                                if (o_value.column == value) {
                                    let name = key;
                                    let new_index = nameIndexDict[name];
                                    newOrder[o_index].column = new_index;
                                }
                            })    
                        })
                        d.order = newOrder;
                    }
                },
                dom: 'lBfrtip',
                columns: columns,
                processing: true,
            }
        }
    },
}
</script>
