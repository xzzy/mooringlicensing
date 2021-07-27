<template lang="html">
    <FormSection label="Search Person" Index="search_person">
        <div class="row form-group">
                <label for="person_lookup" class="col-sm-3 control-label">Person</label>
                <div class="col-sm-6">
                    <select 
                        id="person_lookup"  
                        name="person_lookup"  
                        ref="person_lookup" 
                        class="form-control" 
                    />
                </div>
                <div class="col-sm-3">
                    <input 
                    type="button" 
                    @click.prevent="openDetailsApprovalsVessels" 
                    class="btn btn-primary" 
                    value="View Details"
                    />
                </div>
        </div>

    </FormSection>
</template>

<script>
import FormSection from '@/components/forms/section_toggle.vue'
var select2 = require('select2');
require("select2/dist/css/select2.min.css");
require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
    export default {
        name:'SearchPerson',
        components:{
            FormSection,
        },
         data:function () {
            return {
                email_user: null,
             }
        },
        computed: {
        },
        methods:{
            openDetailsApprovalsVessels: function() {
                this.$nextTick(() => {
                    if (this.email_user) {
                        window.location.replace("/internal/person/" + this.email_user.id);

                        //this.$router.push({
                        //    name: 'internal-person-detail',
                        //    params: {"email_user": this.email_user},
                        //});
                    }
                });

            },
            initialisePersonLookup: function(){
                let vm = this;
                $(vm.$refs.person_lookup).select2({
                    minimumInputLength: 2,
                    "theme": "bootstrap",
                    allowClear: true,
                    placeholder:"Select Person",
                    ajax: {
                        url: api_endpoints.person_lookup,
                        //url: api_endpoints.vessel_rego_nos,
                        dataType: 'json',
                        data: function(params) {
                            console.log(params)
                            var query = {
                                term: params.term,
                                type: 'public',
                            }
                            return query;
                        },
                    },
                }).
                on("select2:select", function (e) {
                    var selected = $(e.currentTarget);
                    vm.email_user = e.params.data
                }).
                on("select2:unselect",function (e) {
                    var selected = $(e.currentTarget);
                    vm.approval_id = null;
                }).
                on("select2:open",function (e) {
                    //const searchField = $(".select2-search__field")
                    const searchField = $('[aria-controls="select2-person_lookup-results"]')
                    // move focus to select2 field
                    searchField[0].focus();
                });
            },
        },
        mounted: function () {
            this.$nextTick(async () => {
                this.initialisePersonLookup();
            });
        },
        created: async function() {
        },
    }
</script>

<style lang="css" scoped>
</style>

