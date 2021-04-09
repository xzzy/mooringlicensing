<template lang="html">
    <FormSection label="Mooring details" Index="mooring_authorisation">
        <div class="row form-group">
            <label for="" class="col-sm-9 control-label">Do you want to be authorised
            </label>
        </div>
        <div class="form-group">
            <div class="row">
                <div class="col-sm-9">
                    <input type="radio" id="site_licensee" value="site_licensee" v-model="mooringAuthPreference" required=""/>
                    <label for="site_licensee" class="control-label">By a mooring site licensee for their mooring</label>
                </div>
            </div>
            <div class="row">
                <div class="col-sm-9">
                    <input type="radio" id="ria" value="ria" v-model="mooringAuthPreference" required=""/>
                    <label for="ria" class="control-label">By Rottnest Island Authority for a mooring allocated by the Authority</label>
                </div>
            </div>
        </div>

        <div v-if="mooringAuthPreference==='ria'" class="row form-group">
            <draggable class="col-sm-6" v-model="mooringBays">
                    <div class="form-control" id="mooringList" v-for="mooring in mooringBays" :key="mooring.id">
                        {{ mooring.name }}
                    </div>
            </draggable>
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
import draggable from 'vuedraggable';

    export default {
        name:'MooringAuthorisation',
        components:{
            FormSection,
            draggable,
        },
        props:{
            proposal:{
                type: Object,
                required:true
            }
        },
        data:function () {
            return {
                mooringBays: [],
                mooringAuthPreference: null,
            }
        },
        computed: {
        },
        watch: {
        },
        methods:{
            fetchMooringBays: async function(){
                const response = await this.$http.get(api_endpoints.mooring_bays);
                // reorder array based on proposal.bay_preferences_numbered
                if (this.proposal.bay_preferences_numbered) {
                    console.log(this.proposal.bay_preferences_numbered);
                    let newArray = [];
                    for (let n of this.proposal.bay_preferences_numbered) {
                        const found = response.body.find(el => el.id === n);
                        newArray.push(found);
                    }
                    // read ordered array into Vue array
                    for (let bay of newArray) {
                        this.mooringBays.push(bay);
                    }
                } else {
                    for (let bay of response.body) {
                        this.mooringBays.push(bay);
                    }
                }
            },
        },
        mounted:function () {
            this.$nextTick(async () => {
                await this.fetchMooringBays();

            });

        },
    }
</script>

<style lang="css" scoped>
</style>

