<template>
    <div class="container" id="MooringsDash">
        <FormSection :formCollapse="false" label="Moorings" Index="moorings">

        </FormSection>
    </div>
</template>

<script>
import FormSection from "@/components/forms/section_toggle.vue"
export default {
    name: 'InternalMooringsDashboard',
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

