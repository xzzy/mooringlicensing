<template>
    <transition>
        <div v-if="shown" class="panel panel-default">
            <div class="panel-body">
                <div class="delete_arrival_icon">
                    <i class="fa fa-times-circle fa-2x" style="color:coral" @click="delete_arrival_icon_clicked"></i>
                </div>

                <div class="row form-group">
                    <label for="" class="col-sm-2 control-label">Arrival</label>
                    <div class="col-sm-3 input-group date" ref="arrivalDatePicker">
                        <input type="text" class="form-control text-center" placeholder="DD/MM/YYYY"/>
                        <span class="input-group-addon">
                            <span class="glyphicon glyphicon-calendar"></span>
                        </span>
                    </div>
                </div>
                <div class="row form-group">
                    <label for="" class="col-sm-2 control-label">Private visit</label>
                    <div class="col-sm-2">
                        <input type="radio" id="private_yes" name="private_visit" value="true" v-model="arrival.private_visit"/>
                        <label class="radio-inline control-label" for="private_yes">Yes</label>
                    </div>
                    <div class="col-sm-2">
                        <input type="radio" id="private_no" name="private_visit" value="false" v-model="arrival.private_visit"/>
                        <label class="radio-inline control-label" for="private_no">No</label>
                    </div>
                </div>
                <div class="row form-group">
                    <div class="col-sm-2"></div>
                    <div class="col-sm-2 text-center"><label>Landing</label></div>
                    <div class="col-sm-2 text-center"><label>Extended stay</label></div>
                    <div class="col-sm-2 text-center"><label>Not landing</label></div>
                    <div class="col-sm-2 text-center"><label>Approved events</label></div>
                </div>
                <div class="row form-group">
                    <div class="col-sm-2"><label>Number of Adults</label><br />(12 and over)</div>
                    <div class="col-sm-2">
                        <input type="number" min="0" max="100" step="1" class="form-control text-center" name="adults-landing" placeholder="" v-model="arrival.adults.landing">
                    </div>
                    <div class="col-sm-2">
                        <input type="number" min="0" max="100" step="1" class="form-control text-center" name="adults-extended-stay" placeholder="" v-model="arrival.adults.extended_stay">
                    </div>
                    <div class="col-sm-2">
                        <input type="number" min="0" max="100" step="1" class="form-control text-center" name="adults-not-landing" placeholder="" v-model="arrival.adults.not_landing">
                    </div>
                    <div class="col-sm-2">
                        <input type="number" min="0" max="100" step="1" class="form-control text-center" name="adults-approved-events" placeholder="" v-model="arrival.adults.approved_events">
                    </div>
                </div>
                <div class="row form-group">
                    <div class="col-sm-2"><label>Number of Children</label><br />(4 - 12)</div>
                    <div class="col-sm-2">
                        <input type="number" min="0" max="100" step="1" class="form-control text-center" name="children-landing" placeholder="" v-model="arrival.children.landing">
                    </div>
                    <div class="col-sm-2">
                        <input type="number" min="0" max="100" step="1" class="form-control text-center" name="children-extended-stay" placeholder="" v-model="arrival.children.extended_stay">
                    </div>
                    <div class="col-sm-2">
                        <input type="number" min="0" max="100" step="1" class="form-control text-center" name="children-not-landing" placeholder="" v-model="arrival.children.not_landing">
                    </div>
                    <div class="col-sm-2">
                        <input type="number" min="0" max="100" step="1" class="form-control text-center" name="children-approved-events" placeholder="" v-model="arrival.children.approved_events">
                    </div>
                </div>
            </div>
        </div>
    </transition>
</template>

<script>
import 'eonasdan-bootstrap-datetimepicker';
import datatable from '@/utils/vue/datatable.vue'
import FormSection from "@/components/forms/section_toggle.vue"
import { api_endpoints, helpers } from '@/utils/hooks'
  
export default {
    name: 'DcvAdmissionArrivalPanel',
    props: {
        level: {
            type: String,
            default: 'external',
        },
        uuid: null,
        arrival: null,
    },
    data() {
        let vm = this
        return {
            shown: false,  // Hidden first to make fade-in work
            paySubmitting: false,
        }
    },
    components:{
        FormSection,
    },
    watch: {

    },
    computed: {
        is_external: function() {
            return this.level == 'external'
        },
        csrf_token: function() {
          return helpers.getCookie('csrftoken')
        },
    },
    methods: {
        delete_arrival_icon_clicked: function() {
            this.shown = false
            this.$emit('delete_arrival', this.arrival.uuid)
        },
        addEventListeners: function () {
            let vm = this;
            let el_fr = $(vm.$refs.arrivalDatePicker);
            let options = {
                format: "DD/MM/YYYY",
                showClear: true ,
                useCurrent: false,
            };

            el_fr.datetimepicker(options);

            el_fr.on("dp.change", function(e) {
                let selected_date = null;
                if (e.date){
                    // Date selected
                    selected_date = e.date.format('DD/MM/YYYY')  // e.date is moment object
                    vm.arrival.arrival_date = selected_date;
                } else {
                    // Date not selected
                    vm.arrival.arrival_date = selected_date;
                }
            });
        },
    },
    mounted: function () {
        this.shown = true  // Show the panel once
    },
    created: function() {
        this.$nextTick(() => {
            this.addEventListeners();
        });
    },
}
</script>

<style>
.mb-1 {
    margin: 0 0 1em 0;
}
.mb-2 {
    margin: 0 0 2em 0;
}
.panel-body {
    position: relative;
}
.delete_arrival_icon {
    position: absolute;
    top: 0;
    right: 0;
    cursor: pointer;
}
.v-enter, .v-leave-to {
    opacity: 0;
}
.v-enter-active, .v-leave-active {
    transition: 0.8s;
}
.v-enter-to, .v-leave {
    opacity: 1;
}
</style>
