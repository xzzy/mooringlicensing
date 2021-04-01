<template lang="html">
    <FormSection label="Preferred mooring area" Index="preferred_mooring_area">
        <div class="row form-group">
            <label for="" class="col-sm-9 control-label">Select one preferred mooring area. Preference cannot be changed without losing your original application date.</label>
        </div>
        <div class="row form-group">
            <div class="col-sm-6" v-for="mooring in moorings">
                <input type="radio" name="mooring_name" :value="mooring" v-model="selectedMooring" required="">
                    {{ mooring }}
                </input>
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
                selectedMooring: null,
                moorings: [
                    'Catherine Bay',
                    'Longreach Bay',
                    'Narrow Neck (Rocky Bay)',
                    'Stark Bay',
                    'Geordie Bay',
                    'Majorie Bay',
                    'Porpoise Bay',
                    'Thomson Bay',
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

