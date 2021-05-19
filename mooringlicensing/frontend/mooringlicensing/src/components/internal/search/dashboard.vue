<template>
    <div class="container" id="SearchDash">
        <FormSection :formCollapse="false" label="Search Persons" Index="search_persons">

        </FormSection>
        <FormSection :formCollapse="false" label="Search Vessels" Index="search_vessels">

        </FormSection>
        <FormSection :formCollapse="false" label="Search Mooring" Index="search_mooring">

        </FormSection>
        <FormSection :formCollapse="false" label="Search Sticker Number" Index="search_sticker_number">

        </FormSection>
        <FormSection :formCollapse="false" label="Search Reference Number" Index="search_reference_number">

        </FormSection>
        <FormSection :formCollapse="false" label="Search Keyword" Index="search_keyword">

        </FormSection>
    </div>
</template>

<script>
import FormSection from "@/components/forms/section_toggle.vue"
export default {
    name: 'InternalSearch',
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

