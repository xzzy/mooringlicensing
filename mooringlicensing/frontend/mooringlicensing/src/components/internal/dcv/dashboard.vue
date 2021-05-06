<template>
    <div class="container" id="dcvDash">
        <FormSection :formCollapse="false" label="DCV Permits" Index="dcv_permits">

        </FormSection>
        <FormSection :formCollapse="false" label="DCV Admission Fees" Index="dcv_admission_fees">

        </FormSection>
    </div>
</template>

<script>
import FormSection from "@/components/forms/section_toggle.vue"
export default {
    name: 'ExternalDashboard',
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

