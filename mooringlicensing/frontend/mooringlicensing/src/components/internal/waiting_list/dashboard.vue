<template>
    <div class="container" id="WaitingListDash">
        <FormSection :formCollapse="false" label="Waiting List" Index="waiting_list">
            <WaitingListTable 
                level="internal"
            />
        </FormSection>
    </div>
</template>

<script>
import FormSection from "@/components/forms/section_toggle.vue"
import WaitingListTable from "@/components/common/table_waiting_list"

export default {
    name: 'InternalWaigintListDashboard',
    data() {
        let vm = this;
        return {

        }
    },
    components:{
        FormSection,
        WaitingListTable,
    },
    methods: {

    },
}
</script>

