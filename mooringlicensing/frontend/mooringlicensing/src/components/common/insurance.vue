<template lang="html">
    <FormSection label="Insurance details" Index="insurance_details">
        <div class="row form-group">
            <label for="" class="col-sm-9 control-label">The nominated vessel has
            </label>
        </div>
        <div class="row form-group">
            <div class="col-sm-9" v-for="choice in insuranceChoices">
                <input type="radio" name="insuranceChoice" :id="choice.code" :value="choice.code" required=""/>
                <label :for="choice.code">{{ choice.description }}</label>
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
        name:'Insurance',
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
                selectedOption: null,
                insuranceChoices: [],
            }
        },
        computed: {
        },
        methods:{
            fetchInsuranceChoices: async function(){
                const response = await this.$http.get(api_endpoints.insurance_choices_dict);
                for (let choice of response.body) {
                    this.insuranceChoices.push(choice);
                }
            },
            addEventHandlers: function() {
                let vm = this;
                for (let choice of vm.insuranceChoices) {
                    let choiceSelector = '#' + choice.code;
                    $(choiceSelector).on('change', (e) => {
                        vm.selectedOption = e.currentTarget.value
                    });
                }
            },
        },
        mounted:function () {
            this.$nextTick(async () => {
                await this.fetchInsuranceChoices();
                this.addEventHandlers();
                // read selectedOption from proposal
                let vm = this;
                if (this.proposal.insurance_choice) {
                    this.selectedOption = this.proposal.insurance_choice;
                    let selected = $('#' + vm.selectedOption);
                    selected.prop('checked', true).trigger('change');
                }
            });
        },
        created: async function() {
        },
    }
</script>

<style lang="css" scoped>
</style>

