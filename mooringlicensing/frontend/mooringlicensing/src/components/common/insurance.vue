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
                /*
                fiveMillion: null,
                tenMillion: null,
                over10: null,
                */
            }
        },
        computed: {
            /*
            availableInsurance: function() {
                return [
                    {
                        cover: "fiveMillion",
                        description: "$5 million Third Party Liability insurance cover - required for vessels of length less than 6.4 metres",
                    },
                    {
                        cover: "tenMillion",
                        description: "$10 million Third Party Liability insurance cover - required for vessels of length 6.4 metres or greater",
                    },
                    {
                        cover: "over10",
                        description: "over $10 million",
                    },
                    ]
            },
            */
        },
        methods:{
            fetchInsuranceChoices: async function(){
                const response = await this.$http.get(api_endpoints.insurance_choices_dict);
                /*
                let choices = [];
                let ii = 0;
                for (let res of response.body){
                    choices.splice(ii++, 0, res);
                }
                let i = 0;
                console.log(choices);
                for (let choice of choices) {
                    this.insuranceChoices.splice(i++, 0, choice);
                }
                */
                for (let choice of response.body) {
                    this.insuranceChoices.push(choice);
                }
            },
            addEventHandlers: function() {
                let vm = this;
                /*
                console.log(vm.insuranceChoices[0])
                console.log(vm.insuranceChoices)
                */
                for (let choice of vm.insuranceChoices) {
                    let choiceSelector = '#' + choice.code;
                    //console.log(choiceSelector)
                    $(choiceSelector).on('change', (e) => {
                        //console.log(e.currentTarget.value)
                        vm.selectedOption = e.currentTarget.value
                    });
                }
                /*
                const fiveMillion = $('#fiveMillion');
                fiveMillion.on('change', (e) => {
                    console.log(e.currentTarget.value)
                    vm.selectedOption = e.currentTarget.value
                });
                const tenMillion = $('#tenMillion');
                tenMillion.on('change', (e) => {
                    console.log(e.currentTarget.value)
                    vm.selectedOption = e.currentTarget.value
                });
                const over10 = $('#over10');
                over10.on('change', (e) => {
                    console.log(e.currentTarget.value)
                    vm.selectedOption = e.currentTarget.value
                });
                */
            },
        },
        mounted:function () {
            this.$nextTick(async () => {
                await this.fetchInsuranceChoices();
                this.addEventHandlers();
            });
        },
        created: async function() {
        },
    }
</script>

<style lang="css" scoped>
</style>

