<template>
    <div class="container" id="approvalsDash">
        <FormSection :formCollapse="false" label="Approvals" Index="approvals">
            <ApprovalsTable
                level="internal"
            />
        </FormSection>
    </div>
</template>

<script>
import FormSection from "@/components/forms/section_toggle.vue"
import ApprovalsTable from "@/components/common/table_approvals.vue"

export default {
    name: 'InternalApprovalsDashboard',
    data() {
        let vm = this;
        return {

        }
    },
    components:{
        FormSection,
        ApprovalsTable,
    },
    methods: {

    },
}
</script>

