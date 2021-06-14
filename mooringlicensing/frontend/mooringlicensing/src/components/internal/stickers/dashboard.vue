<template>
    <div class="container" id="StickersDash">
        <FormSection :formCollapse="false" label="Stickers" Index="stickers">
            <StickersTable
                level="internal"
                @actionClicked="actionClicked"
            />
        </FormSection>
        <ModalDetails
            ref="modal_details" 
            @sendData="sendData"
        />
    </div>
</template>

<script>
import FormSection from "@/components/forms/section_toggle.vue"
import StickersTable from "@/components/common/table_stickers.vue"
import ModalDetails from "@/components/internal/stickers/modal_details.vue"
import { api_endpoints, helpers } from '@/utils/hooks'
import uuid from 'uuid'

export default {
    name: 'InternalStickersDashboard',
    data() {
        let vm = this;
        return {
            uuid: uuid()
        }
    },
    components:{
        FormSection,
        StickersTable,
        ModalDetails,
    },
    methods: {
        actionClicked: function(param){
            this.$refs.modal_details.action = param.action
            this.$refs.modal_details.sticker.id = param.id
            this.$refs.modal_details.key = uuid()
            this.$refs.modal_details.isModalOpen = true
        },
        sendData: function(params){
            console.log('sendData')
            console.log(params.details)
            let vm = this
            let action = params.action
            vm.$http.post(helpers.add_endpoint_json(api_endpoints.stickers, params.sticker.id + '/' + action), params.details).then(
                res => {
                    vm.updateStatusCell(params.sticker.id, res.body.sticker.status)
                    vm.$refs.modal_details.close()
                },
                err => {
                    console.log(err)
                    vm.$refs.modal_details.close()
                }
            )
        },
        updateStatusCell: function(id, newStatus){
            console.log('in updateStatusCell')
        }
    },
}
</script>

