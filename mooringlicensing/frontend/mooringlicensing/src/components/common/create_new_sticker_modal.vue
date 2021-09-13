<template lang="html">
    <div id="change-contact">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="title" large>
            <div class="container-fluid">
                <alert :show.sync="showError" type="danger"><strong>{{ errorString }}</strong></alert>
                <div class="row form-group">
                    <label class="col-sm-2 control-label" for="sticker_number">Sticker Number</label>
                    <div class="col-sm-3">
                        <input type="number" class="col-sm-9 form-control" name="sticker_number" id="sticker_number" v-model="sticker_number" />
                    </div>
                </div>
                <div class="row form-group">
                    <label class="col-sm-2 control-label" for="sticker_number">Mailed Date</label>
                    <div class="col-sm-3">
                        <div class="input-group date" ref="mailedDatePicker">
                            <input type="text" class="form-control text-center" placeholder="DD/MM/YYYY" id="mailed_date_elem"/>
                            <span class="input-group-addon">
                                <span class="glyphicon glyphicon-calendar"></span>
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            <div slot="footer">
                <button type="button" v-if="processing" disabled class="btn btn-default" @click="ok"><i class="fa fa-spinner fa-spin"></i> Processing</button>
                <button type="button" v-else class="btn btn-default" @click="ok" :disabled="!okButtonEnabled">Ok</button>
                <button type="button" class="btn btn-default" @click="cancel">Cancel</button>
            </div>
        </modal>
    </div>
</template>

<script>
import modal from '@vue-utils/bootstrap-modal.vue'
import alert from '@vue-utils/alert.vue'
import { helpers, api_endpoints, constants } from "@/utils/hooks.js"

export default {
    name:'RequestNewStickerModal',
    components:{
        modal,
        alert,
    },
    props:{

    },
    data:function () {
        let vm = this;
        return {
            dcv_permit_id: null,
            isModalOpen:false,
            sticker_number: '',
            mailed_date: null,
            processing: false,

            errors: false,
            errorString: '',
        }
    },
    watch: {
        dcv_permit_id: async function(){
            let vm = this

            //if (vm.approval_id){
            //    const ret = await vm.$http.get(helpers.add_endpoint_json(api_endpoints.approvals, vm.approval_id + '/stickers'))
            //    for (let sticker of ret.body.stickers){
            //        sticker.checked = false
            //    }
            //    vm.stickers = ret.body.stickers

            //} else {
            //    vm.stickers = []
            //}
        }
    },
    computed: {
        okButtonEnabled: function(){
            if(this.sticker_number && this.mailed_date){
                return true
            }
            return false
        },
        showError: function() {
            var vm = this;
            return vm.errors;
        },
        title: function() {
            return 'Create New Sticker'
        },
    },
    methods:{
        ok:function () {
            let vm =this;
            vm.errors = false
            vm.processing = true
            vm.$emit("sendData", {
                "sticker_number": vm.sticker_number,
                "dcv_permit_id": vm.dcv_permit_id,
                "mailed_date": vm.mailed_date,
            })
        },
        cancel:function () {
            this.close();
        },
        close:function () {
            this.isModalOpen = false
            this.sticker_number = ''
            this.mailed_date = null
            $('#mailed_date_elem').val('')
            this.errors = false
            this.processing = false
            this.dcv_permit_id = null
        },
        addEventListeners: function () {
            let vm = this;
            let options = {
                format: "DD/MM/YYYY",
                showClear: true ,
                useCurrent: false,
            };

            // Mailed Date
            let el_mailed = $(vm.$refs.mailedDatePicker);
            el_mailed.datetimepicker(options);
            el_mailed.on("dp.change", function(e) {
                let selected_date = null;
                if (e.date){
                    selected_date = e.date.format('DD/MM/YYYY')  // e.date is moment object
                }
                vm.mailed_date = selected_date;
            });
        },
        fetchData: function(){
            let vm = this

            //vm.$http.get(api_endpoints.fee_item_sticker_replacement).then(
            //    (response) => {
            //        vm.fee_item = response.body
            //    },
            //    (error) => {
            //        console.log(error)
            //    }
            //)
        }
    },
    created:function () {
        this.fetchData()
        this.$nextTick(() => {
            this.addEventListeners();
        });
    }
}
</script>

<style lang="css">
</style>
