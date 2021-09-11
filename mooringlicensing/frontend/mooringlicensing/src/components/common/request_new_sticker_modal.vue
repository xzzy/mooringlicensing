<template lang="html">
    <div id="change-contact">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="title" large>
            <div class="container-fluid">
                <alert :show.sync="showError" type="danger"><strong>{{ errorString }}</strong></alert>
                <div class="row form-group">
                    <table class="table table-striped table-bordered">
                        <thead>
                            <tr>
                                <th scope="col"></th>
                                <th scope="col">Number</th>
                                <th scope="col">vessel</th>
                                <th scope="col">mooring</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="sticker in stickers" :key="sticker.id">
                                <td><input type="checkbox" v-model="sticker.checked" /></td>
                                <td>{{ sticker.number }}</td>
                                <td>---</td>
                                <td>---</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class="row form-group">
                    <label class="col-sm-2 control-label" for="reason">Reason</label>
                    <div class="col-sm-9">
                        <textarea class="col-sm-9 form-control" name="reason" v-model="details.reason"></textarea>
                    </div>
                </div>
            </div>
            <div slot="footer">
                <span><strong>Sticker replacement cost ${{ total_fee }}</strong></span>
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
            approval_id: null,
            stickers: [],
            isModalOpen:false,
            action: '',
            sticker: {},
            details: vm.getDefaultDetails(),
            processing: false,

            //form:null,
            errors: false,
            //validation_form: null,
            errorString: '',
            //successString: '',
            //success:false,
        }
    },
    watch: {
        approval_id: async function(){
            let vm = this
            // Whenever approval_id is changed, this function is called
            console.log('vm.approval_id')
            console.log(vm.approval_id)


            if (vm.approval_id){
                const ret = await vm.$http.get(helpers.add_endpoint_json(api_endpoints.approvals, vm.approval_id + '/stickers'))
                for (let sticker of ret.body.stickers){
                    sticker.checked = false
                }
                vm.stickers = ret.body.stickers

            } else {
                vm.stickers = []
            }
        }
    },
    computed: {
        okButtonEnabled: function(){
            if (this.details.reason){
                for (let sticker of this.stickers){
                    if (sticker.checked === true){
                        return true
                    }
                }
            }
            return false
        },
        showError: function() {
            var vm = this;
            return vm.errors;
        },
        title: function() {
            return 'New Sticker'
        },
        total_fee: function() {
            return 12
        }
    },
    methods:{
        getDefaultDetails: function(){
            return {
                reason: '',
                date_of_lost_sticker: null,
                date_of_returned_sticker: null,
            }
        },
        ok:function () {
            let vm =this;
            vm.errors = false
            vm.processing = true
            vm.$emit("sendData", {
                "details": vm.details,
                "approval_id": vm.approval_id,
                "stickers": vm.stickers,
            })
        },
        cancel:function () {
            this.close();
        },
        close:function () {
            this.isModalOpen = false
            this.details = this.getDefaultDetails()
            $('#returned_date_elem').val('')
            $('#lost_date_elem').val('')
            this.errors = false
            this.processing = false
            this.approval_id = null
            //$('.has-error').removeClass('has-error');
            //this.validation_form.resetForm();
        },
        addEventListeners: function () {
            let vm = this;
            let options = {
                format: "DD/MM/YYYY",
                showClear: true ,
                useCurrent: false,
            };

            // Date of Lost
            let el_lost = $(vm.$refs.lostDatePicker);
            el_lost.datetimepicker(options);
            el_lost.on("dp.change", function(e) {
                let selected_date = null;
                if (e.date){
                    // Date selected
                    selected_date = e.date.format('DD/MM/YYYY')  // e.date is moment object
                    vm.details.date_of_lost_sticker = selected_date;
                } else {
                    // Date not selected
                    vm.details.date_of_lost_sticker = selected_date;
                }
            });

            // Date of Returned
            let el_returned = $(vm.$refs.returnedDatePicker)
            el_returned.datetimepicker(options);
            el_returned.on("dp.change", function(e) {
                let selected_date = null;
                if (e.date){
                    // Date selected
                    selected_date = e.date.format('DD/MM/YYYY')  // e.date is moment object
                    vm.details.date_of_returned_sticker = selected_date;
                } else {
                    // Date not selected
                    vm.details.date_of_returned_sticker = selected_date;
                }
            });
        },
        //addFormValidations: function() {
        //    let vm = this;
        //    vm.validation_form = $(vm.form).validate({
        //        rules: {
        //            reason:"required",
        //        },
        //        messages: {
        //            arrival:"field is required",
        //            departure:"field is required",
        //            campground:"field is required",
        //            campsite:"field is required"
        //        },
        //        showErrors: function(errorMap, errorList) {
        //            $.each(this.validElements(), function(index, element) {
        //                var $element = $(element);
        //                $element.attr("data-original-title", "").parents('.form-group').removeClass('has-error');
        //            });
        //            // destroy tooltips on valid elements
        //            $("." + this.settings.validClass).tooltip("destroy");
        //            // add or update tooltips
        //            for (var i = 0; i < errorList.length; i++) {
        //                var error = errorList[i];
        //                $(error.element)
        //                    .tooltip({
        //                        trigger: "focus"
        //                    })
        //                    .attr("data-original-title", error.message)
        //                    .parents('.form-group').addClass('has-error');
        //            }
        //        }
        //    });
        //},
    },
    created:function () {
        this.$nextTick(() => {
            this.addEventListeners();
        });
    }
}
</script>

<style lang="css">
</style>
