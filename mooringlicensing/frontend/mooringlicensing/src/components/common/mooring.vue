<template lang="html">
    <FormSection label="Preferred mooring area" Index="preferred_mooring_area">
        <div class="row form-group">
            <label for="" class="col-sm-3 control-label">Select one preferred mooring area.</label>
        </div>
        <div class="row form-group">
            <div class="col-sm-2" v-for="mooring in moorings">
                {{ mooring }}
            </div>
        </div>
    </FormSection>
</template>

<script>
import FormSection from '@/components/forms/section_toggle.vue'
    export default {
        name:'mooring',
        components:{
            FormSection,
        },
        props:{
            proposal:{
                type: Object,
                required:true
            }
        },
        data:function () {
            return {
                moorings: [
                    'catherine',
                    'longreach',
                    'narrow',
                    'stark',
                    'geordie',
                    'majorie',
                    'porpoise',
                    'thomson'
                ],
            }
        },
        computed: {
        },
        methods:{
        },
        mounted:function () {
        }
    }
</script>

<style lang="css" scoped>
</style>

