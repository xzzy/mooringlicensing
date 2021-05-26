<template>
    <div class="container">
        <FormSection 
            :formCollapse="false" 
            label="Other documents" 
            Index="other_documents"
        >
            <div class="row form-group">
                <label for="" class="col-sm-5 control-label">Copy of current mooring report</label>
                <div class="col-sm-7">
                    <FileField 
                        ref="mooring_report_documents"
                        name="mooring-report-documents"
                        :isRepeatable="true"
                        :documentActionUrl="mooring_report_url"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row form-group">
                <label for="" class="col-sm-5 control-label">Written proof of finalisation concerning the ownership of the mooring apparatus between you and the previous licensee</label>
                <div class="col-sm-7">
                    <FileField 
                        ref="written_proof_documents"
                        name="written-proof-documents"
                        :isRepeatable="true"
                        :documentActionUrl="written_proof_url"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </FormSection>
    </div>
</template>

<script>
import FormSection from "@/components/forms/section_toggle.vue"
import FileField from '@/components/forms/filefield_immediate.vue'
import { api_endpoints, helpers } from '@/utils/hooks'

export default {
    name: 'OtherDocuments',
    data() {
        let vm = this;
        return {
            uuid: '',
        }
    },
    components:{
        FormSection,
        FileField,
    },
    computed: {
        mooring_report_url: function() {
            let url = '';
            if (this.uuid){
                url = helpers.add_endpoint_join(
                    api_endpoints.proposal_by_uuid,
                    this.uuid + '/process_mooring_report_document/'
                )
            }
            return url;
        },
        written_proof_url: function() {
            let url = '';
            if (this.uuid){
                url = helpers.add_endpoint_join(
                    api_endpoints.proposal_by_uuid,
                    this.uuid + '/process_written_proof_document/'
                )
            }
            return url;
        },

    },
    mounted: function(){
        this.uuid = this.$route.params.uuid
    }
}
</script>
