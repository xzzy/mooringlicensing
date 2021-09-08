<template>
    <div class="container" id="SearchDash">

        <SearchPerson />
        <SearchVessel />
        <SearchMooring />
        <SearchSticker />

        <FormSection :formCollapse="false" label="Search Reference Number" Index="search_reference_number">
        </FormSection>

        <FormSection :formCollapse="false" label="Search Keyword" Index="search_keyword">
        </FormSection>
    </div>
</template>

<script>
import FormSection from "@/components/forms/section_toggle.vue"
import SearchMooring from "./search_mooring.vue"
import SearchVessel from "./search_vessel.vue"
import SearchSticker from "./search_sticker.vue"
import SearchPerson from "./search_person.vue"

export default {
    name: 'InternalSearch',
    data() {
        let vm = this;
        return {

        }
    },
    components:{
        FormSection,
        SearchMooring,
        SearchVessel,
        SearchSticker,
        SearchPerson,
    },
    methods: {

    },
}
</script>

