<template>
    <div class="container" id="StickersDash">
        <FormSection :formCollapse="false" label="Stickers" Index="stickers">
            <StickersTable
                level="internal"
            />
        </FormSection>
    </div>
</template>

<script>
import FormSection from "@/components/forms/section_toggle.vue"
import StickersTable from "@/components/common/table_stickers.vue"

export default {
    name: 'InternalStickersDashboard',
    data() {
        let vm = this;
        return {

        }
    },
    components:{
        FormSection,
        StickersTable,
    },
    methods: {

    },
}
</script>

