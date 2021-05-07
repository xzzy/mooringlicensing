<template>
    <div class="container" id="approvalsDash">
        <FormSection :formCollapse="false" label="Approvals" Index="approvals">

        </FormSection>
    </div>
</template>

<script>
import FormSection from "@/components/forms/section_toggle.vue"
export default {
    name: 'InternalApprovalsDashboard',
    data() {
        let vm = this;
        return {

        }
    },
    components:{
        FormSection,
    },
    methods: {

    },
}
</script>

