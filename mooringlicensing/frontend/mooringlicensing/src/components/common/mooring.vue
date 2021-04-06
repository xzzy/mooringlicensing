<template lang="html">
    <FormSection label="Preferred mooring area" Index="preferred_mooring_area">
        <div class="row form-group">
            <label for="" class="col-sm-9 control-label">Select one preferred mooring area. Preference cannot be changed without losing your original application date.</label>
        </div>
        <div class="row form-group">
            <div class="col-sm-6" v-for="mooring in mooringBays">
                <label :for="mooring.id" class="col-sm-5 control-label">{{ mooring.name }}</label>
                <input type="radio" :id="mooring.id" :value="mooring" v-model="selectedMooring" required=""/>
            </div>
        </div>
    </FormSection>
</template>

<script>
import FormSection from '@/components/forms/section_toggle.vue'
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'

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
                mooringBays: [],
                /*
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
                */
            }
        },
        computed: {
        },
        methods:{
            fetchMooringBays: async function(){
                const response = await this.$http.get(api_endpoints.mooring_bays);
                for (let bay of response.body) {
                    this.mooringBays.push(bay)
                }
            },
        },
        mounted:function () {
            this.$nextTick(async () => {
                await this.fetchMooringBays();
                // read in currently selected preference from Proposal
                if (this.proposal.preferred_bay_id) {
                    console.log("preferred bay");
                    for (let bay of this.mooringBays) {
                        if (bay.id === this.proposal.preferred_bay_id) {
                            this.selectedMooring = Object.assign({}, bay);
                        }
                    }
                }
            });

        }
    }
</script>

<style lang="css" scoped>
</style>

