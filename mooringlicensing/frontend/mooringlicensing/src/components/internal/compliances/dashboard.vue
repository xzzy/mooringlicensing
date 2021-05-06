<template>
    <div class="container" id="compliancesDash">
        <FormSection :formCollapse="false" label="Compliances" Index="compliances">

        </FormSection>
    </div>
</template>

<script>
import FormSection from "@/components/forms/section_toggle.vue"
export default {
    name: 'InternalCompliancesDashboard',
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

