<template>
    <div class="container" id="StickersDash">
        <FormSection :formCollapse="false" label="Stickers" Index="stickers">

        </FormSection>
    </div>
</template>

<script>
import FormSection from "@/components/forms/section_toggle.vue"
export default {
    name: 'InternalStickersDashboard',
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

